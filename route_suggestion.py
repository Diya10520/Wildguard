"""
route_suggestion.py
Smart Route Suggestion System — avoids known animal crossing hotspots.

For a hackathon demo we don't need a full routing engine (OSRM/Google Directions).
We simulate it: given a start/end and known high-risk zones, we check if the
straight-line path passes near a hotspot and, if so, propose a simple detour
waypoint offset from the hotspot.
"""
import math


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _point_to_segment_distance_m(p, a, b):
    # Approximate using equirectangular projection (fine for short local routes)
    lat0 = math.radians(a[0])
    def proj(pt):
        x = math.radians(pt[1]) * math.cos(lat0) * 6371000
        y = math.radians(pt[0]) * 6371000
        return x, y

    px, py = proj(p)
    ax, ay = proj(a)
    bx, by = proj(b)

    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)

    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    closest = (ax + t * dx, ay + t * dy)
    return math.hypot(px - closest[0], py - closest[1])


def suggest_route(start: tuple, end: tuple, hotspots: list, avoid_radius_m: float = 300):
    """
    start, end: (lat, lon)
    hotspots: list of {lat, lon, risk_level, count}
    Returns a route as a list of waypoints, plus which hotspots were avoided.
    """
    high_risk_hotspots = [h for h in hotspots if h.get("risk_level") == "High"]

    dangerous_nearby = []
    for h in high_risk_hotspots:
        dist = _point_to_segment_distance_m((h["lat"], h["lon"]), start, end)
        if dist < avoid_radius_m:
            dangerous_nearby.append(h)

    if not dangerous_nearby:
        return {
            "route": [start, end],
            "avoided_hotspots": [],
            "message": "Direct route is clear of known high-risk animal crossing zones.",
        }

    waypoints = [start]
    for h in dangerous_nearby:
        # offset perpendicular-ish by shifting lat/lon slightly away from hotspot
        offset_lat = h["lat"] + (0.004 if h["lat"] < end[0] else -0.004)
        offset_lon = h["lon"] + (0.004 if h["lon"] < end[1] else -0.004)
        waypoints.append((offset_lat, offset_lon))
    waypoints.append(end)

    return {
        "route": waypoints,
        "avoided_hotspots": dangerous_nearby,
        "message": f"Rerouted to avoid {len(dangerous_nearby)} high-risk animal crossing zone(s).",
    }
