from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeterProfile:
    id: str
    name: str
    category: str
    base_kw: float
    peak_kw: float
    power_factor: float


@dataclass
class Telemetry:
    timestamp: str
    building_id: str
    meter_id: str
    meter_name: str
    category: str
    voltage: float
    current: float
    frequency: float
    power_kw: float
    reactive_kvar: float
    apparent_kva: float
    power_factor: float
    energy_kwh: float
    demand_kw: float
    quality: str = "GOOD"
