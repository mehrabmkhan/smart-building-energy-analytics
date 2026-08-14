# Industrial Protocol Pipeline

The demo contains these stages:

- multiple meter simulator profiles
- Modbus-style edge collection snapshots
- MQTT-shaped topic publishing: `building/{building_id}/meter/{meter_id}/telemetry`
- telemetry processor validation and persistence
- SQLite demo time-series store
- analytics and alert engine
- FastAPI dashboard and report export

Docker Compose includes an actual Mosquitto broker and PostgreSQL database for a more distributed local architecture. The free public deployment keeps services inside one process to avoid paid infrastructure.
