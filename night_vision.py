"""
night_vision.py
AI preprocessing for low-light / fog / rain conditions to improve detection accuracy.
Uses CLAHE (Contrast Limited Adaptive Histogram Equalization) for low light and a
simple dark-channel-inspired dehaze for fog/rain clarity — lightweight, no extra
model needed, ideal for a hackathon demo.
"""
import cv2
import numpy as np


def estimate_lighting(frame: np.ndarray) -> str:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    if brightness < 60:
        return "night"
    if brightness < 110:
        return "low_light"
    return "daylight"


def enhance_low_light(frame: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    merged = cv2.merge((l_enhanced, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def dehaze(frame: np.ndarray, strength: float = 0.6) -> np.ndarray:
    """Simple contrast-stretch based dehaze — fast approximation for demo purposes."""
    img = frame.astype(np.float32) / 255.0
    dark_channel = np.min(img, axis=2)
    atmosphere = np.percentile(dark_channel, 95)
    transmission = 1 - strength * (dark_channel / (atmosphere + 1e-6))
    transmission = np.clip(transmission, 0.3, 1.0)
    result = np.empty_like(img)
    for c in range(3):
        result[:, :, c] = (img[:, :, c] - atmosphere) / transmission + atmosphere
    result = np.clip(result * 255, 0, 255).astype(np.uint8)
    return result


def preprocess(frame: np.ndarray):
    """
    Full pipeline: detect lighting condition, apply appropriate enhancement.
    Returns (enhanced_frame, lighting_condition_str)
    """
    lighting = estimate_lighting(frame)
    if lighting in ("night", "low_light"):
        frame = enhance_low_light(frame)
        frame = dehaze(frame, strength=0.4)
    return frame, lighting
