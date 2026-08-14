import pytest

from powersight.analytics import calculate_analytics, detect_anomalies, evaluate_alerts
from powersight.config import load_meter_profiles
from powersight.pipeline import PipelineService
from powersight.simulator import BuildingMeterSimulator
from powersight.store import latest_by_meter, recent_telemetry


def test_multi_meter_simulator_generates_realistic_values() -> None:
    building_id, profiles = load_meter_profiles()
    readings = BuildingMeterSimulator(building_id, profiles).read_modbus_snapshot()

    assert len(readings) == 6
    assert all(item.power_kw > 0 for item in readings)
    assert all(59.5 < item.frequency < 60.5 for item in readings)


@pytest.mark.asyncio
async def test_end_to_end_pipeline_persists_telemetry(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("POWERSIGHT_DB", str(tmp_path / "powersight.db"))
    service = PipelineService()

    await service.poll_once()
    rows = recent_telemetry()

    assert len(rows) == 6
    assert latest_by_meter()[0]["meter_name"]


def test_analytics_calculate_building_demand(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("POWERSIGHT_DB", str(tmp_path / "powersight.db"))
    service = PipelineService()
    import asyncio

    asyncio.run(service.poll_once())
    result = calculate_analytics(recent_telemetry())

    assert result["current_demand_kw"] > 0
    assert result["meters_online"] == 6


def test_power_quality_alerts_detect_low_pf() -> None:
    alerts = evaluate_alerts({"meter_id": "test", "power_factor": 0.82, "voltage": 600, "frequency": 60, "demand_kw": 100})

    assert alerts[0]["alert_type"] == "Low PF"


def test_anomaly_detector_returns_list() -> None:
    rows = [
        {"id": i, "meter_id": "m1", "meter_name": "Meter 1", "timestamp": str(i), "power_kw": 100 + i % 3}
        for i in range(25)
    ]
    rows.append({"id": 26, "meter_id": "m1", "meter_name": "Meter 1", "timestamp": "26", "power_kw": 180})

    assert detect_anomalies(rows)
