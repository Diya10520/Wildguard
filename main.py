"""
main.py
FastAPI backend for the AI Roadside Wildlife Collision Prevention System.

Endpoints:
  POST /api/detect/video     -> start processing an uploaded/local video, streams
                                 results over the /ws WebSocket in real time
  POST /api/detect/frame     -> run detection on a single uploaded image (quick test)
  POST /api/report           -> crowd-sourced animal sighting report
  GET  /api/incidents        -> incident log
  GET  /api/heatmap          -> aggregated risk heatmap points
  GET  /api/analytics        -> dashboard analytics (species, risk mix, hourly)
  GET  /api/route-suggestion -> safer route avoiding hotspots
  WS   /ws                   -> live stream of detections/alerts to the dashboard

Run:
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8000
"""
import asyncio
import json
import random
import time
from datetime import datetime
from typing import List, Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database as db
import night_vision
from detector import AnimalDetector
from risk_engine import risk_engine
from route_suggestion import suggest_route

app = FastAPI(title="Wildlife Collision Prevention API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()
detector = AnimalDetector()  # loads yolov8n.pt (downloads once, ~6MB)

# ---------------------------------------------------------------------------
# WebSocket connection manager — pushes live detections/alerts to the dashboard
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.disconnect(d)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive; frontend doesn't need to send anything.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Simulated GPS + road/lighting context (swap for real GPS/IoT sensors later)
# ---------------------------------------------------------------------------
# A handful of demo "zones" along a fictional highway so the heatmap has spread.
DEMO_ZONES = [
    {"lat": 12.9716, "lon": 77.5946, "road_type": "highway"},
    {"lat": 12.9750, "lon": 77.6010, "road_type": "forest_road"},
    {"lat": 12.9800, "lon": 77.6100, "road_type": "rural"},
    {"lat": 12.9650, "lon": 77.5890, "road_type": "highway"},
]


def simulate_context():
    zone = random.choice(DEMO_ZONES)
    speed = round(random.uniform(40, 100), 1)
    jitter = lambda v: v + random.uniform(-0.0015, 0.0015)
    return {
        "lat": jitter(zone["lat"]),
        "lon": jitter(zone["lon"]),
        "road_type": zone["road_type"],
        "vehicle_speed": speed,
    }


# ---------------------------------------------------------------------------
# Core pipeline: frame -> night vision preprocess -> detect -> risk -> log -> broadcast
# ---------------------------------------------------------------------------
async def process_frame(frame: np.ndarray):
    enhanced, lighting = night_vision.preprocess(frame)
    detections = detector.detect(enhanced)

    results = []
    for d in detections:
        ctx = simulate_context()
        distance_m = detector.estimate_distance_m(d["area_ratio"])

        prediction = risk_engine.predict(
            speed_kmh=ctx["vehicle_speed"],
            distance_m=distance_m,
            road_type=ctx["road_type"],
            lighting=lighting,
            size_weight=d["size_weight"],
            lat=ctx["lat"],
            lon=ctx["lon"],
        )

        incident = {
            "timestamp": datetime.utcnow().isoformat(),
            "animal_type": d["label"],
            "confidence": d["confidence"],
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "lat": ctx["lat"],
            "lon": ctx["lon"],
            "road_type": ctx["road_type"],
            "lighting": lighting,
            "vehicle_speed": ctx["vehicle_speed"],
            "distance_m": distance_m,
            "outcome": "risk_avoided",
        }
        incident_id = db.log_incident(incident)
        incident["id"] = incident_id

        alert_message = build_alert_message(d["label"], distance_m, prediction["risk_level"])
        payload = {
            "type": "detection",
            "incident": incident,
            "alert": alert_message,
            "time_to_reach_s": prediction["time_to_reach_s"],
        }
        results.append(payload)
        await manager.broadcast(payload)

        if prediction["risk_level"] == "High":
            await manager.broadcast({
                "type": "emergency",
                "message": f"🚨 HIGH RISK: {d['label']} on {ctx['road_type']} — "
                           f"broadcasting warning to nearest control center.",
                "incident": incident,
            })

    return results


def build_alert_message(animal: str, distance_m: float, risk_level: str) -> str:
    base = f"{animal.capitalize()} detected {int(distance_m)}m ahead"
    if risk_level == "High":
        return f"⚠️ HIGH COLLISION RISK — {base}. Slow down immediately."
    if risk_level == "Medium":
        return f"⚠️ {base}. Reduce speed."
    return f"ℹ️ {base}."


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------
@app.post("/api/detect/frame")
async def detect_frame(file: UploadFile = File(...)):
    contents = await file.read()
    npimg = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if frame is None:
        return {"error": "Could not decode image"}
    results = await process_frame(frame)
    return {"detections": results}


@app.post("/api/detect/video")
async def detect_video(file: UploadFile = File(...), frame_skip: int = 5):
    """
    Processes an uploaded video frame-by-frame (skipping frames for speed),
    streaming each detection to connected WebSocket clients as it happens.
    This runs as a background task so the HTTP call returns immediately.
    """
    contents = await file.read()
    tmp_path = f"/tmp/{int(time.time())}_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(contents)

    asyncio.create_task(run_video_pipeline(tmp_path, frame_skip))
    return {"status": "processing_started", "note": "Watch the /ws stream for live results."}


async def run_video_pipeline(path: str, frame_skip: int):
    cap = cv2.VideoCapture(path)
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        if frame_count % frame_skip != 0:
            continue
        await process_frame(frame)
        await asyncio.sleep(0.05)  # yield control, simulate near-real-time pacing
    cap.release()
    await manager.broadcast({"type": "video_complete", "message": "Video processing complete."})


class SightingReport(BaseModel):
    animal_type: str
    lat: float
    lon: float
    reported_by: Optional[str] = "anonymous"


@app.post("/api/report")
async def report_sighting(report: SightingReport):
    db.log_sighting(report.animal_type, report.lat, report.lon, report.reported_by)
    await manager.broadcast({
        "type": "crowd_report",
        "message": f"👀 Community report: {report.animal_type} spotted nearby.",
        "report": report.model_dump(),
    })
    return {"status": "logged"}


@app.get("/api/incidents")
async def get_incidents(limit: int = 200):
    return db.get_incidents(limit)


@app.get("/api/heatmap")
async def get_heatmap():
    return db.get_heatmap_points()


@app.get("/api/analytics")
async def get_analytics():
    return db.get_analytics()


@app.get("/api/route-suggestion")
async def route_suggestion(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float
):
    hotspots = db.get_heatmap_points()
    result = suggest_route((start_lat, start_lon), (end_lat, end_lon), hotspots)
    return result


@app.post("/api/reinforce")
async def reinforce(lat: float, lon: float, was_real_incident: bool):
    """Feedback loop: driver confirms/dismisses an alert -> RL-style zone weight update."""
    risk_engine.reinforce(lat, lon, was_real_incident)
    return {"status": "updated"}


@app.get("/")
async def root():
    return {"status": "online", "service": "Wildlife Collision Prevention API"}
