from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd


DEFAULT_DB = Path("data/powersight.db")


def db_path() -> Path:
    return Path(os.getenv("POWERSIGHT_DB", str(DEFAULT_DB)))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_store() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                building_id TEXT NOT NULL,
                meter_id TEXT NOT NULL,
                meter_name TEXT NOT NULL,
                category TEXT NOT NULL,
                voltage REAL NOT NULL,
                current REAL NOT NULL,
                frequency REAL NOT NULL,
                power_kw REAL NOT NULL,
                reactive_kvar REAL NOT NULL,
                apparent_kva REAL NOT NULL,
                power_factor REAL NOT NULL,
                energy_kwh REAL NOT NULL,
                demand_kw REAL NOT NULL,
                quality TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                meter_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                value REAL NOT NULL,
                status TEXT NOT NULL,
                reason TEXT NOT NULL
            );
            """
        )
        conn.commit()


def insert_telemetry(payload: dict) -> None:
    initialize_store()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO telemetry (
                timestamp, building_id, meter_id, meter_name, category, voltage, current, frequency,
                power_kw, reactive_kvar, apparent_kva, power_factor, energy_kwh, demand_kw, quality
            ) VALUES (:timestamp, :building_id, :meter_id, :meter_name, :category, :voltage, :current, :frequency,
                :power_kw, :reactive_kvar, :apparent_kva, :power_factor, :energy_kwh, :demand_kw, :quality)
            """,
            payload,
        )
        conn.commit()


def insert_alert(alert: dict) -> None:
    initialize_store()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO alerts (timestamp, meter_id, severity, alert_type, value, status, reason)
            VALUES (:timestamp, :meter_id, :severity, :alert_type, :value, :status, :reason)
            """,
            alert,
        )
        conn.commit()


def recent_telemetry(limit: int = 500) -> list[dict]:
    initialize_store()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in reversed(rows)]


def latest_by_meter() -> list[dict]:
    initialize_store()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT t.* FROM telemetry t
            JOIN (SELECT meter_id, MAX(id) id FROM telemetry GROUP BY meter_id) latest
            ON t.id = latest.id
            ORDER BY t.meter_name
            """
        ).fetchall()
    return [dict(row) for row in rows]


def recent_alerts(limit: int = 50) -> list[dict]:
    initialize_store()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def telemetry_frame(limit: int = 1000) -> pd.DataFrame:
    return pd.DataFrame(recent_telemetry(limit))
