"""
risk_engine.py
Collision Risk Prediction Engine.

Combines: vehicle speed, animal distance, road type, lighting condition,
and animal size to output a 0-100 risk score + Low/Medium/High label.

Also includes a lightweight "reinforcement-learning-style" adaptive layer:
zones that repeatedly produce real incidents get their weight nudged up,
zones that produce false alarms get nudged down. This is a simplified
online-learning stand-in that is easy to explain to judges without
needing an actual RL training loop.
"""
import math
from collections import defaultdict

ROAD_RISK = {
    "highway": 0.9,
    "rural": 0.75,
    "forest_road": 1.0,
    "urban": 0.4,
}

LIGHTING_RISK = {
    "daylight": 0.3,
    "low_light": 0.7,
    "night": 1.0,
}


class RiskEngine:
    def __init__(self):
        # zone_key -> learned multiplier (starts neutral at 1.0)
        self.zone_weights = defaultdict(lambda: 1.0)

    @staticmethod
    def _zone_key(lat: float, lon: float, precision: int = 3) -> str:
        return f"{round(lat, precision)},{round(lon, precision)}"

    def predict(self, *, speed_kmh: float, distance_m: float, road_type: str,
                lighting: str, size_weight: float, lat: float, lon: float) -> dict:
        road_factor = ROAD_RISK.get(road_type, 0.6)
        light_factor = LIGHTING_RISK.get(lighting, 0.6)

        # Time-to-reach animal at current speed (seconds) — lower = higher risk
        speed_ms = max(speed_kmh, 1) * 1000 / 3600
        time_to_reach = distance_m / speed_ms if speed_ms > 0 else 999
        urgency = max(0.0, min(1.0, 1 - (time_to_reach / 8)))  # <8s to impact = urgent

        base_score = (
            0.35 * urgency +
            0.20 * road_factor +
            0.20 * light_factor +
            0.25 * size_weight
        )

        zone_key = self._zone_key(lat, lon)
        adaptive_score = base_score * self.zone_weights[zone_key]
        risk_score = round(min(adaptive_score, 1.0) * 100, 1)

        if risk_score >= 70:
            level = "High"
        elif risk_score >= 40:
            level = "Medium"
        else:
            level = "Low"

        return {
            "risk_score": risk_score,
            "risk_level": level,
            "time_to_reach_s": round(time_to_reach, 1),
            "zone_key": zone_key,
            "zone_weight": round(self.zone_weights[zone_key], 2),
        }

    def reinforce(self, lat: float, lon: float, was_real_incident: bool):
        """Call this when ground truth is known (e.g. driver confirms/dismisses alert)."""
        zone_key = self._zone_key(lat, lon)
        if was_real_incident:
            self.zone_weights[zone_key] = min(self.zone_weights[zone_key] + 0.1, 1.8)
        else:
            self.zone_weights[zone_key] = max(self.zone_weights[zone_key] - 0.05, 0.5)


# Singleton used across the app
risk_engine = RiskEngine()
