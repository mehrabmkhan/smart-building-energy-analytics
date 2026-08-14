from __future__ import annotations

from pathlib import Path

import yaml

from .models import MeterProfile


def load_meter_profiles(path: str | Path = "config/meters.yaml") -> tuple[str, list[MeterProfile]]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return raw["building_id"], [MeterProfile(**item) for item in raw["meters"]]
