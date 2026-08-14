from __future__ import annotations

import asyncio
from dataclasses import asdict

from .analytics import evaluate_alerts
from .bus import LocalMqttBus
from .config import load_meter_profiles
from .simulator import BuildingMeterSimulator
from .store import initialize_store, insert_alert, insert_telemetry


class PipelineService:
    def __init__(self) -> None:
        building_id, profiles = load_meter_profiles()
        self.simulator = BuildingMeterSimulator(building_id, profiles)
        self.bus = LocalMqttBus()
        self.running = False
        self.collector_task: asyncio.Task | None = None
        self.processor_task: asyncio.Task | None = None
        self.messages_failed = 0
        self.last_message = ""

    async def start(self) -> None:
        initialize_store()
        self.running = True
        self.collector_task = asyncio.create_task(self._collector_loop())
        self.processor_task = asyncio.create_task(self._processor_loop())

    async def stop(self) -> None:
        self.running = False
        for task in [self.collector_task, self.processor_task]:
            if task:
                task.cancel()

    async def _collector_loop(self) -> None:
        while self.running:
            for telemetry in self.simulator.read_modbus_snapshot():
                await self.bus.publish_telemetry(telemetry)
            await asyncio.sleep(1)

    async def _processor_loop(self) -> None:
        while self.running:
            try:
                topic, payload = await self.bus.next_message()
                self.last_message = topic
                insert_telemetry(payload)
                for alert in evaluate_alerts(payload):
                    insert_alert(alert)
            except Exception:
                self.messages_failed += 1

    async def poll_once(self) -> None:
        for telemetry in self.simulator.read_modbus_snapshot():
            payload = asdict(telemetry)
            insert_telemetry(payload)
            for alert in evaluate_alerts(payload):
                insert_alert(alert)

    def health(self) -> dict:
        return {
            "modbus_devices": "ONLINE",
            "mqtt_broker": "ONLINE",
            "telemetry_processor": "ONLINE" if self.running else "STOPPED",
            "database": "ONLINE",
            "published_messages": self.bus.published,
            "consumed_messages": self.bus.consumed,
            "failed_messages": self.messages_failed,
            "last_message": self.last_message,
        }
