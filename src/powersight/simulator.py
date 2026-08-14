from __future__ import annotations

import math
import time
from datetime import UTC, datetime

from .models import MeterProfile, Telemetry


class BuildingMeterSimulator:
    def __init__(self, building_id: str, profiles: list[MeterProfile]) -> None:
        self.building_id = building_id
        self.profiles = profiles
        self.started = time.monotonic()
        self.energy: dict[str, float] = {item.id: 1000.0 + index * 250 for index, item in enumerate(profiles)}
        self.last = time.monotonic()

    def read_modbus_snapshot(self) -> list[Telemetry]:
        now = time.monotonic()
        elapsed_h = max(now - self.last, 0) / 3600
        runtime = now - self.started
        self.last = now
        readings = []
        for index, profile in enumerate(self.profiles):
            hour = (runtime / 20 + index * 2) % 24
            occupied = 1.0 if 7 <= hour <= 18 else 0.28
            hvac_bump = 0.35 * math.sin(runtime / 11 + index)
            event = 0.25 if profile.category == "equipment" and int(runtime) % 57 < 8 else 0.0
            load = min(1.0, max(0.08, occupied + hvac_bump + event))
            kw = profile.base_kw + (profile.peak_kw - profile.base_kw) * load
            if profile.id == "server-room":
                kw = profile.base_kw + 12 * math.sin(runtime / 30)
            pf = max(0.78, min(0.99, profile.power_factor + 0.025 * math.sin(runtime / 17 + index)))
            voltage = 600 * (1 + 0.008 * math.sin(runtime / 23 + index))
            kva = kw / pf
            kvar = math.sqrt(max(kva**2 - kw**2, 0))
            current = kva * 1000 / (math.sqrt(3) * voltage)
            frequency = 60 + 0.035 * math.sin(runtime / 19 + index)
            self.energy[profile.id] += kw * elapsed_h
            readings.append(
                Telemetry(
                    timestamp=datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    building_id=self.building_id,
                    meter_id=profile.id,
                    meter_name=profile.name,
                    category=profile.category,
                    voltage=round(voltage, 2),
                    current=round(current, 2),
                    frequency=round(frequency, 3),
                    power_kw=round(kw, 3),
                    reactive_kvar=round(kvar, 3),
                    apparent_kva=round(kva, 3),
                    power_factor=round(pf, 4),
                    energy_kwh=round(self.energy[profile.id], 4),
                    demand_kw=round(kw * (1 + 0.08 * math.sin(runtime / 13)), 3),
                )
            )
        return readings
