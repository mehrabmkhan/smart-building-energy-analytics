from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from powersight.analytics import calculate_analytics, detect_anomalies, observations
from powersight.pipeline import PipelineService
from powersight.store import latest_by_meter, recent_alerts, recent_telemetry


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
service = PipelineService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await service.start()
    yield
    await service.stop()


app = FastAPI(title="PowerSight Analytics", version="1.0.0", lifespan=lifespan)


def context() -> dict:
    rows = recent_telemetry(720)
    analytics = calculate_analytics(rows)
    alerts = recent_alerts(25)
    anomalies = detect_anomalies(rows)
    return {
        "latest": latest_by_meter(),
        "rows": rows[-120:],
        "analytics": analytics,
        "alerts": alerts,
        "anomalies": anomalies,
        "observations": observations(analytics, anomalies, alerts),
        "health": service.health(),
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "dashboard.html", context())


@app.get("/api/telemetry")
def api_telemetry() -> list[dict]:
    return recent_telemetry(500)


@app.get("/api/meters")
def api_meters() -> list[dict]:
    return latest_by_meter()


@app.get("/api/analytics")
def api_analytics() -> dict:
    rows = recent_telemetry(720)
    analytics = calculate_analytics(rows)
    anomalies = detect_anomalies(rows)
    alerts = recent_alerts(25)
    return {"analytics": analytics, "anomalies": anomalies, "alerts": alerts, "observations": observations(analytics, anomalies, alerts)}


@app.get("/api/health")
def api_health() -> dict:
    return service.health()


@app.get("/reports/daily.html")
def daily_report() -> Response:
    data = context()
    html = templates.get_template("report.html").render(data)
    return Response(html, media_type="text/html", headers={"Content-Disposition": "attachment; filename=powersight_daily_report.html"})
