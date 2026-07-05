# 🐾 AI Roadside Wildlife Collision Prevention System
### TATA Hackathon — Edge AI + IoT + Cloud Analytics

A real-time system that detects animals on roads, predicts collision risk, and
alerts drivers — with a live analytics dashboard.

---

## 🏗️ Architecture

```
[Video/CCTV feed] → [Night Vision Preprocessing] → [YOLOv8 Detection]
        → [Risk Prediction Engine] → [SQLite Incident Log]
        → [WebSocket broadcast] → [React Dashboard: Heatmap + Alerts + Analytics]
```

| Layer | Tech |
|---|---|
| Detection | YOLOv8 (ultralytics), OpenCV |
| Backend / API | FastAPI, WebSockets, SQLite |
| Frontend | React (Vite), Leaflet.js, Chart.js |
| "Edge AI simulation" | Backend processes frames locally before any cloud analytics step — narrate this as your edge layer in the demo |

## ✅ Features implemented (from your spec)

- AI-based animal detection (YOLOv8, COCO animal classes: cow, dog, elephant, horse, sheep, bear, zebra, giraffe, bird, cat)
- Collision risk prediction engine (speed, distance, road type, lighting → Low/Medium/High)
- Smart risk heatmap (Leaflet, live-updating from SQLite)
- Driver alert system (dashboard alert + simulated audio via browser speech synthesis for High risk)
- Night vision / low-light & fog enhancement module (CLAHE + dehaze, auto-triggered by brightness)
- Incident logging (SQLite: time, GPS, animal, outcome)
- Reinforcement-learning-style adaptive zone weighting (`/api/reinforce`)
- Crowd-sourced sighting reports (`/api/report`)
- Smart route suggestion avoiding high-risk zones (`/api/route-suggestion`)
- Analytics dashboard (species breakdown, risk mix, hourly activity)
- Emergency response trigger simulation (broadcast on High risk detections)

---

## ▶️ Run it (VS Code — two terminals)

### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
First run auto-downloads `yolov8n.pt` (~6MB, needs internet once).

Backend docs/testing: http://localhost:8000/docs

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

---

## 🎬 Demo script for judges

1. Open the dashboard (http://localhost:5173) — show the empty heatmap/analytics.
2. In **"Run Detection"**, upload a short dashcam/animal video clip (or a single image with an animal — try any cow/dog/horse photo).
3. Watch **Live Alerts** populate in real time via WebSocket, including audio warning for High risk.
4. Point out the **Heatmap** updating with colored risk zones.
5. Scroll to **Analytics** — species breakdown, risk mix, peak activity chart.
6. Hit **"Report sighting nearby"** to demo the crowd-sourced feature.
7. Call `GET /api/route-suggestion?start_lat=..&start_lon=..&end_lat=..&end_lon=..` in `/docs` to show smart rerouting around high-risk zones.
8. Explain the **night vision module**: it auto-detects frame brightness and applies CLAHE + dehaze before detection — mention this is what boosts accuracy in fog/rain/night, tying into your "Predictive Wildlife Movement Modeling" differentiator (the risk engine's per-zone adaptive weights are the seed of that predictive layer).

---

## 🗂️ Where to plug in what you already built

- If you already have a working YOLOv8 test script, replace the model loading
  in `backend/detector.py` (`AnimalDetector.__init__`) with your trained/custom
  weights path.
- If your React scaffold already has routing/pages, copy the components from
  `frontend/src/components/` into your existing app and wire the same
  `ws://localhost:8000/ws` connection shown in `App.jsx`.

## 📌 Notes / good judge talking points

- Distance estimation uses a bounding-box-size heuristic — accurate enough for
  a demo; in production you'd calibrate per camera or fuse with a depth sensor/LiDAR.
- The "reinforcement learning" is a simplified online-weight-update model — explain
  it as the prototype of a full RL system trained on real incident outcomes.
- SQLite is used for the hackathon; swap for Postgres/cloud DB in production
  and this is literally a one-line change in `database.py` (connection string).
