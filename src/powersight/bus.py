from __future__ import annotations

import asyncio
import json
from dataclasses import asdict

from .models import Telemetry


class LocalMqttBus:
    """In-process MQTT-shaped bus for the public demo and tests."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()
        self.published = 0
        self.consumed = 0

    async def publish_telemetry(self, telemetry: Telemetry) -> None:
        topic = f"building/{telemetry.building_id}/meter/{telemetry.meter_id}/telemetry"
        await self.queue.put((topic, asdict(telemetry)))
        self.published += 1

    async def next_message(self) -> tuple[str, dict]:
        topic, payload = await self.queue.get()
        json.loads(json.dumps(payload))
        self.consumed += 1
        return topic, payload
