from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd


def calculate_analytics(rows: list[dict]) -> dict:
    if not rows:
        return {
            "current_demand_kw": 0,
            "today_energy_kwh": 0,
            "peak_demand_kw": 0,
            "average_pf": 0,
            "meters_online": 0,
            "energy_by_meter": [],
            "load_factor": 0,
        }
    frame = pd.DataFrame(rows)
    latest = frame.sort_values("id").groupby("meter_id").tail(1)
    current_demand = float(latest["power_kw"].sum())
    peak = float(frame.groupby("timestamp")["power_kw"].sum().max())
    energy_by_meter = latest[["meter_name", "energy_kwh", "power_kw", "category"]].to_dict("records")
    return {
        "current_demand_kw": round(current_demand, 2),
        "today_energy_kwh": round(float(latest["energy_kwh"].sum()), 2),
        "peak_demand_kw": round(peak, 2),
        "average_pf": round(float(latest["power_factor"].mean()), 3),
        "meters_online": int(latest["meter_id"].nunique()),
        "energy_by_meter": energy_by_meter,
        "load_factor": round(current_demand / peak, 3) if peak else 0,
    }


def evaluate_alerts(payload: dict) -> list[dict]:
    alerts = []
    checks = [
        (payload["power_factor"] < 0.90, "WARNING", "Low PF", payload["power_factor"], "Power factor below 0.90."),
        (payload["voltage"] < 570 or payload["voltage"] > 635, "WARNING", "Voltage Outside Threshold", payload["voltage"], "Voltage outside 600 V +/- about 5%."),
        (payload["frequency"] < 59.7 or payload["frequency"] > 60.3, "INFO", "Frequency Outside Threshold", payload["frequency"], "Frequency outside expected band."),
        (payload["demand_kw"] > 550, "CRITICAL", "High Demand", payload["demand_kw"], "Demand exceeds configured demo threshold."),
    ]
    for tripped, severity, alert_type, value, reason in checks:
        if tripped:
            alerts.append(
                {
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "meter_id": payload["meter_id"],
                    "severity": severity,
                    "alert_type": alert_type,
                    "value": round(float(value), 4),
                    "status": "ACTIVE",
                    "reason": reason,
                }
            )
    return alerts


def detect_anomalies(rows: list[dict]) -> list[dict]:
    if len(rows) < 20:
        return []
    frame = pd.DataFrame(rows)
    anomalies = []
    for meter_id, group in frame.groupby("meter_id"):
        mean = group["power_kw"].mean()
        std = group["power_kw"].std() or 1
        latest = group.sort_values("id").tail(1).iloc[0]
        z = abs((latest["power_kw"] - mean) / std)
        if z > 2.2:
            anomalies.append(
                {
                    "meter": latest["meter_name"],
                    "timestamp": latest["timestamp"],
                    "score": round(float(z), 2),
                    "measurement": "power_kw",
                    "value": round(float(latest["power_kw"]), 2),
                    "expected_range": f"{round(mean - 2 * std, 1)} to {round(mean + 2 * std, 1)} kW",
                    "reason": "Latest power is outside its rolling statistical band.",
                }
            )
    return anomalies


def observations(analytics: dict, anomalies: list[dict], alerts: list[dict]) -> list[str]:
    notes = [
        f"Current building demand is {analytics['current_demand_kw']} kW with a load factor of {analytics['load_factor']}.",
        f"Average power factor across online meters is {analytics['average_pf']}.",
    ]
    if anomalies:
        first = anomalies[0]
        notes.append(f"{first['meter']} is outside its expected range at {first['value']} kW.")
    if alerts:
        notes.append(f"{len(alerts)} active or recent alerts require review.")
    return notes
