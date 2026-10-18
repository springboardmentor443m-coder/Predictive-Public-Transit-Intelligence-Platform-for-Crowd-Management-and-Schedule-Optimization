"""
MetroFlow - AI Platform for Metro Crowd Management and Scheduling

Run:   python -m uvicorn app.main:app --reload --port 8000
Docs:  http://127.0.0.1:8000/docs        Dashboard: http://127.0.0.1:8000/dashboard
"""
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional
import csv
import io
import os

from fastapi import FastAPI

app = FastAPI()

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from app.core.security import (
    Token, UserProfile, authenticate_user, create_access_token, get_current_user, require_admin,
)
from app.data import repository as repo
from app.services import ai_prediction, alerts, analytics, crowd_monitoring, scheduling, live_simulation, operations_store

app = FastAPI(
    title="MetroFlow API",
    description="AI Platform for Metro Crowd Management and Scheduling",
    version="1.0.0",
)
_allowed_origins = [x.strip() for x in os.getenv("METROFLOW_ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_allowed_origins, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])

STATIC_DIR = Path(__file__).parent / "static"
User = Annotated[UserProfile, Depends(get_current_user)]
Admin = Annotated[UserProfile, Depends(require_admin)]
HourQ = Annotated[int, Query(ge=0, le=23, description="Hour of day, 0-23")]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def _parse_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="Date must be in YYYY-MM-DD format")


def date_any(on_date: Annotated[str, Query(description="YYYY-MM-DD (any date, used for forecasts)")]) -> str:
    return _parse_date(on_date)


def date_in_data(on_date: Annotated[str, Query(description="YYYY-MM-DD within the recorded data")]) -> str:
    value = _parse_date(on_date)
    df = repo.load_data()
    if not ((df["Date"].min() <= pd.Timestamp(value)) and (pd.Timestamp(value) <= df["Date"].max())):
        raise HTTPException(
            status_code=404,
            detail=f"No recorded data for {value}. Available: {df['Date'].min().date()} to {df['Date'].max().date()}")
    return value


def date_optional(on_date: Optional[str] = None) -> str:
    return date_in_data(on_date) if on_date else repo.latest_date()


DateAny = Annotated[str, Depends(date_any)]
DateData = Annotated[str, Depends(date_in_data)]
DateOpt = Annotated[str, Depends(date_optional)]


def authorize_station(station: str, user: UserProfile) -> str:
    """404 for unknown stations; operators may only access their assigned station."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    if user.role == "operator" and user.assigned_station != station:
        raise HTTPException(status_code=403, detail=f"Operators can only access {user.assigned_station}")
    return station


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------
@app.get("/", tags=["System"])
def root():
    return {"message": "MetroFlow API is running. Visit /docs for interactive API docs, /dashboard for the UI."}


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "dataset_latest_date": repo.latest_date(), "station_count": len(repo.list_stations()),
            "models_trained": ai_prediction.DEMAND_MODEL_PATH.exists(), "mode": "demo", "real_time_connected": False}


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html")


# ---------------------------------------------------------------------------
# Simulated-live demo feed (not a real transit connection)
# ---------------------------------------------------------------------------
@app.get("/simulation/live", tags=["Simulated Live Data"])
def get_simulated_live(user: User):
    """Current simulated snapshot; clearly marked as not real-time transit data."""
    result = live_simulation.get_status()
    if user.role == "operator":
        result["stations"] = [s for s in result["stations"] if s["station"] == user.assigned_station]
        result["alerts"] = [a for a in result["alerts"] if a["station"] == user.assigned_station]
        result["station_count"] = len(result["stations"])
        result["system_total_entries"] = sum(s["entries"] for s in result["stations"])
        result["system_total_exits"] = sum(s["exits"] for s in result["stations"])
        # Do not expose network-wide history aggregates to station-scoped operators.
        result["history"] = []
    return result


@app.post("/simulation/start", tags=["Simulated Live Data"])
def start_simulated_live(user: Admin, interval_seconds: Annotated[int, Query(ge=3, le=60)] = 5):
    """Start the simulated demo stream. Admin-only; interval must be 3–60 seconds."""
    return live_simulation.start(interval_seconds=interval_seconds)


@app.post("/simulation/stop", tags=["Simulated Live Data"])
def stop_simulated_live(user: Admin):
    """Stop refreshing the demo stream. Admin-only."""
    return live_simulation.stop()


class SimulationScenarioIn(BaseModel):
    scenario: str = Field(pattern="^(normal|rush_hour|demand_surge|service_disruption)$")


@app.post("/simulation/scenario", tags=["Simulated Live Data"])
def change_simulation_scenario(payload: SimulationScenarioIn, user: Admin):
    """Change the simulated operating scenario. Admin-only; never changes real trains."""
    return live_simulation.set_scenario(payload.scenario)


@app.get("/simulation/history", tags=["Simulated Live Data"])
def get_simulation_history(user: Admin, limit: Annotated[int, Query(ge=1, le=500)] = 100):
    """Persistent snapshot history. Network-wide aggregates are admin-only."""
    rows = operations_store.history(limit)
    return {"count": len(rows), "history": rows, "storage": "sqlite", "notice": "Historical simulation snapshots, not real-world transit observations."}


@app.get("/simulation/events", tags=["Simulated Live Data"])
def get_simulation_events(user: Admin, limit: Annotated[int, Query(ge=1, le=200)] = 50):
    """Audit trail for simulation start/stop and scenario changes."""
    rows = operations_store.events(limit)
    return {"count": len(rows), "events": rows}


@app.get("/simulation/export.csv", tags=["Simulated Live Data"])
def export_simulation_history(user: Admin, limit: Annotated[int, Query(ge=1, le=500)] = 500):
    """Download persisted simulated-live history as CSV."""
    rows = operations_store.history(limit)
    output = io.StringIO()
    fields = ["id", "tick", "updated_at", "scenario", "system_total_entries", "system_total_exits", "high_crowd_stations", "critical_stations", "alert_count"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=metroflow-simulation-history.csv"})


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------
@app.post("/auth/login", response_model=Token, tags=["User Management"])
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return Token(access_token=create_access_token({"sub": user["username"], "role": user["role"]}))


@app.get("/auth/me", response_model=UserProfile, tags=["User Management"])
def read_profile(user: User):
    return user


@app.get("/admin/ping", tags=["User Management"])
def admin_only(user: Admin):
    return {"message": f"Welcome, {user.full_name}. Admin access confirmed."}


# ---------------------------------------------------------------------------
# Crowd Monitoring
# ---------------------------------------------------------------------------
@app.get("/stations", tags=["Crowd Monitoring"])
def get_stations(user: User):
    stations = repo.list_stations()
    if user.role == "operator":
        stations = [s for s in stations if s == user.assigned_station]
    return {"stations": stations, "count": len(stations)}


@app.get("/stations/capacity", tags=["Crowd Monitoring"])
def get_station_capacity(user: User):
    capacity = repo.load_capacity()
    if user.role == "operator":
        capacity = {k: v for k, v in capacity.items() if k == user.assigned_station}
    return capacity


@app.get("/crowd/live", tags=["Crowd Monitoring"])
def get_live_crowd(user: User, on_date: DateOpt, hour: HourQ = 8):
    snapshot = crowd_monitoring.get_live_snapshot(on_date, hour)
    if user.role == "operator":
        snapshot["stations"] = [s for s in snapshot["stations"] if s["station"] == user.assigned_station]
    return snapshot


@app.get("/crowd/station/{station}", tags=["Crowd Monitoring"])
def get_station_snapshot(station: str, user: User, on_date: DateOpt, hour: HourQ = 8):
    authorize_station(station, user)
    result = repo.station_snapshot(station, on_date, hour)
    if not result:
        raise HTTPException(status_code=404, detail="No data for this station/date/hour")
    return result


@app.get("/crowd/analytics/{station}", tags=["Crowd Monitoring"])
def get_station_crowd_analytics(station: str, user: User, days: Annotated[int, Query(ge=1, le=730)] = 30):
    authorize_station(station, user)
    return crowd_monitoring.get_station_analytics(station, days=days)


@app.get("/crowd/heatmap", tags=["Crowd Monitoring"])
def get_congestion_heatmap(user: User, on_date: DateOpt):
    heatmap = crowd_monitoring.get_heatmap(on_date)
    if user.role == "operator":
        keep = [i for i, s in enumerate(heatmap["stations"]) if s == user.assigned_station]
        heatmap["stations"] = [heatmap["stations"][i] for i in keep]
        heatmap["matrix"] = [heatmap["matrix"][i] for i in keep]
    return heatmap


# ---------------------------------------------------------------------------
# AI Prediction
# ---------------------------------------------------------------------------
@app.post("/ai/train", tags=["AI Prediction"])
def train_ai_models(user: Admin):
    """Re-run the full ML pipeline (cross-validated model selection, test evaluation, refit)."""
    return ai_prediction.train_model()


@app.get("/ai/model-report", tags=["AI Prediction"])
def get_model_report(user: User):
    """Evaluation report: cross-validation table, test metrics vs baseline, intervals, anomaly detector, delay model."""
    return ai_prediction.get_model_metadata()


@app.get("/ai/predict/demand/{station}", tags=["AI Prediction"])
def predict_demand(station: str, user: User, on_date: DateAny, hour: HourQ):
    authorize_station(station, user)
    return ai_prediction.predict_demand(station, on_date, hour)


@app.get("/ai/predict/delay/{station}", tags=["AI Prediction"])
def predict_delay(station: str, user: User, on_date: DateAny, hour: HourQ):
    authorize_station(station, user)
    return ai_prediction.predict_delay(station, on_date, hour)


@app.get("/ai/forecast/{station}", tags=["AI Prediction"])
def get_forecast(station: str, user: User, on_date: DateAny):
    authorize_station(station, user)
    return {"station": station, "date": on_date, "forecast": ai_prediction.forecast_peak_hours(station, on_date)}


@app.get("/ai/recommendations/{station}", tags=["AI Prediction"])
def get_recommendations(station: str, user: User, on_date: DateAny):
    authorize_station(station, user)
    return {"station": station, "date": on_date,
            "recommendations": ai_prediction.smart_recommendations(station, on_date)}


@app.get("/ai/anomalies", tags=["AI Prediction"])
def get_anomalies(user: Admin, on_date: DateData, hour: HourQ):
    """Stations whose recorded entries deviate more than 3 sigma from the forecast."""
    return ai_prediction.detect_anomalies(on_date, hour)


@app.get("/ai/anomaly-check/{station}", tags=["AI Prediction"])
def anomaly_check(station: str, user: User, on_date: DateAny, hour: HourQ,
                  observed_entries: Annotated[float, Query(ge=0, description="Observed passenger count")]):
    """Is an observed passenger count unusual for this station, date and hour?"""
    authorize_station(station, user)
    return ai_prediction.score_observation(station, on_date, hour, observed_entries)


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------
@app.get("/schedule/{station}", tags=["Scheduling"])
def get_schedule(station: str, user: User, on_date: DateAny):
    authorize_station(station, user)
    return {"station": station, "date": on_date, "schedule": scheduling.recommended_schedule(station, on_date)}


@app.get("/schedule/{station}/peak-summary", tags=["Scheduling"])
def get_peak_summary(station: str, user: User, on_date: DateAny):
    authorize_station(station, user)
    return scheduling.peak_hour_summary(station, on_date)


@app.get("/schedule/{station}/delay-report", tags=["Scheduling"])
def get_delay_report(station: str, user: User, days: Annotated[int, Query(ge=1, le=730)] = 90):
    authorize_station(station, user)
    return scheduling.delay_report(station, days=days)


@app.get("/schedule/{station}/adjust-for-delay", tags=["Scheduling"])
def adjust_for_delay(station: str, user: User, on_date: DateAny, hour: HourQ,
                     delay_minutes: Annotated[Optional[float], Query(ge=0, le=180)] = None):
    """Tighten train frequency for a delay. Omit delay_minutes for a model-based scenario."""
    authorize_station(station, user)
    return scheduling.adjust_frequency_for_delay(station, on_date, hour, delay_minutes)


# ---------------------------------------------------------------------------
# Alerts & Notifications
# ---------------------------------------------------------------------------
class EmergencyAnnouncementRequest(BaseModel):
    station: str
    message: str = Field(min_length=3, max_length=500)


@app.get("/alerts/overcrowding", tags=["Alerts"])
def get_overcrowding_alerts(user: User, on_date: DateData, hour: HourQ):
    found = alerts.check_overcrowding_alerts(on_date, hour)
    if user.role == "operator":
        found = [a for a in found if a["station"] == user.assigned_station]
    return {"date": on_date, "hour": hour, "alerts": found}


@app.get("/alerts/forecasted/{station}", tags=["Alerts"])
def get_forecasted_alerts(station: str, user: User, on_date: DateAny):
    authorize_station(station, user)
    return {"station": station, "date": on_date,
            "alerts": alerts.check_forecasted_overcrowding_alerts(station, on_date)}


@app.get("/alerts/delays", tags=["Alerts"])
def get_delay_alerts(user: User, on_date: DateData, hour: HourQ):
    found = alerts.check_delay_alerts(on_date, hour)
    if user.role == "operator":
        found = [a for a in found if a["station"] == user.assigned_station]
    return {"date": on_date, "hour": hour, "alerts": found}


@app.post("/alerts/emergency", tags=["Alerts"])
def post_emergency_announcement(body: EmergencyAnnouncementRequest, user: Admin):
    try:
        return alerts.create_emergency_announcement(body.station, body.message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/alerts/live-feed", tags=["Alerts"])
def get_live_feed(user: Admin, on_date: DateData, hour: HourQ):
    return alerts.real_time_feed(on_date, hour)


# ---------------------------------------------------------------------------
# Analytics Dashboard
# ---------------------------------------------------------------------------
@app.get("/analytics/traffic", tags=["Analytics Dashboard"])
def get_traffic_report(user: Admin, days: Annotated[int, Query(ge=1, le=730)] = 7):
    return analytics.system_traffic_report(days=days)


@app.get("/analytics/station/{station}", tags=["Analytics Dashboard"])
def get_station_performance(station: str, user: User, days: Annotated[int, Query(ge=1, le=730)] = 30):
    authorize_station(station, user)
    return analytics.station_performance_report(station, days=days)


@app.get("/analytics/operational-summary", tags=["Analytics Dashboard"])
def get_operational_summary(user: Admin, on_date: DateData, hour: HourQ):
    return analytics.operational_monitoring_summary(on_date, hour)


@app.get("/analytics/heatmap-report", tags=["Analytics Dashboard"])
def get_heatmap_report(user: Admin, on_date: DateData):
    return analytics.congestion_heatmap_report(on_date)


@app.get("/analytics/ai-insights/{station}", tags=["Analytics Dashboard"])
def get_ai_insights(station: str, user: User, on_date: DateAny):
    authorize_station(station, user)
    return analytics.ai_insights_report(station, on_date)
