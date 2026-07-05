"""
database.py
SQLite persistence layer for incidents (detections) and crowd-sourced sightings.
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "wildlife_safety.db"


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                animal_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                road_type TEXT,
                lighting TEXT,
                vehicle_speed REAL,
                distance_m REAL,
                outcome TEXT DEFAULT 'risk_avoided'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sightings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                animal_type TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                reported_by TEXT DEFAULT 'anonymous'
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def log_incident(data: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO incidents
            (timestamp, animal_type, confidence, risk_score, risk_level,
             lat, lon, road_type, lighting, vehicle_speed, distance_m, outcome)
            VALUES (:timestamp, :animal_type, :confidence, :risk_score, :risk_level,
                    :lat, :lon, :road_type, :lighting, :vehicle_speed, :distance_m, :outcome)
        """, data)
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_incidents(limit: int = 200):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_heatmap_points():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT lat, lon, risk_level, COUNT(*) as count
            FROM incidents GROUP BY lat, lon, risk_level
        """).fetchall()
        return [dict(r) for r in rows]


def log_sighting(animal_type: str, lat: float, lon: float, reported_by: str = "anonymous"):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO sightings (timestamp, animal_type, lat, lon, reported_by)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.utcnow().isoformat(), animal_type, lat, lon, reported_by))
        conn.commit()


def get_sightings(limit: int = 200):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sightings ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_analytics():
    with get_conn() as conn:
        species = conn.execute("""
            SELECT animal_type, COUNT(*) as count FROM incidents
            GROUP BY animal_type ORDER BY count DESC
        """).fetchall()

        risk_dist = conn.execute("""
            SELECT risk_level, COUNT(*) as count FROM incidents
            GROUP BY risk_level
        """).fetchall()

        hourly = conn.execute("""
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM incidents GROUP BY hour ORDER BY hour
        """).fetchall()

        total = conn.execute("SELECT COUNT(*) as c FROM incidents").fetchone()["c"]

        return {
            "total_incidents": total,
            "species_breakdown": [dict(r) for r in species],
            "risk_distribution": [dict(r) for r in risk_dist],
            "hourly_activity": [dict(r) for r in hourly],
        }
