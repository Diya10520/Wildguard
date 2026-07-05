"""
detector.py
AI-Based Animal Detection using YOLOv8 (COCO-pretrained, no custom training needed
for a hackathon demo — COCO already includes cow, horse, sheep, dog, cat, bird,
elephant, bear, zebra, giraffe).
"""
import cv2
import numpy as np
from ultralytics import YOLO

# COCO class ids we care about -> friendly label + relative "size" bucket
ANIMAL_CLASSES = {
    "cow": "large",
    "horse": "large",
    "sheep": "medium",
    "elephant": "very_large",
    "bear": "large",
    "zebra": "large",
    "giraffe": "very_large",
    "dog": "small",
    "cat": "small",
    "bird": "small",
}

SIZE_RISK_WEIGHT = {
    "small": 0.3,
    "medium": 0.55,
    "large": 0.8,
    "very_large": 1.0,
}


class AnimalDetector:
    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.4):
        # yolov8n.pt auto-downloads on first run (needs internet once).
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, frame: np.ndarray):
        """
        Run detection on a single BGR frame.
        Returns list of detections: [{label, confidence, bbox, size_class, box_area_ratio}]
        """
        results = self.model(frame, verbose=False, conf=self.conf_threshold)[0]
        h, w = frame.shape[:2]
        frame_area = h * w

        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = self.model.names[cls_id]
            if label not in ANIMAL_CLASSES:
                continue

            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            box_area = (x2 - x1) * (y2 - y1)
            area_ratio = box_area / frame_area  # bigger box in frame ~= closer animal

            detections.append({
                "label": label,
                "confidence": round(conf, 3),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                "size_class": ANIMAL_CLASSES[label],
                "size_weight": SIZE_RISK_WEIGHT[ANIMAL_CLASSES[label]],
                "area_ratio": round(area_ratio, 4),
            })
        return detections

    @staticmethod
    def estimate_distance_m(area_ratio: float) -> float:
        """
        Rough heuristic: larger bbox area ratio => animal is closer.
        Calibrate this per-camera in a real deployment; fine for a demo.
        """
        area_ratio = max(area_ratio, 0.0005)
        distance = 60 * (0.05 / area_ratio) ** 0.5
        return round(min(max(distance, 2), 150), 1)

    @staticmethod
    def annotate(frame: np.ndarray, detections: list) -> np.ndarray:
        out = frame.copy()
        for d in detections:
            x1, y1, x2, y2 = [int(v) for v in d["bbox"]]
            color = (0, 200, 0)
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            text = f"{d['label']} {d['confidence']:.2f}"
            cv2.putText(out, text, (x1, max(y1 - 8, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return out
