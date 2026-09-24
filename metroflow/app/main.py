"""
MetroFlow - AI Platform for Metro Crowd Management and Scheduling
Delivered through Milestone 3 (Week 5 & 6): Alerts, Notifications & Analytics

Cumulative scope:
  Week 1&2 - User Management, Crowd Monitoring (real per-station capacity)
  Week 3&4 - AI Prediction (demand + delay forecasting), Scheduling Management
  Week 5   - Alert & Notification Module
  Week 6   - Analytics Dashboard Module

Run with:
  uvicorn app.main:app --reload --port 8000
Then open http://127.0.0.1:8000/docs
"""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.security import (
    Token, UserProfile, authenticate_user, create_access_token,
    get_current_user, require_admin,
)
from app.data import repository as repo
from app.services import ai_prediction, alerts, analytics, crowd_monitoring, scheduling

app = FastAPI(
    title="MetroFlow API",
    description="AI Platform for Metro Crowd Management and Scheduling — through Milestone 3 (Week 6)",
    version="0.4.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/", tags=["System"])
def root():
    return {"message": "MetroFlow API is running. Visit /docs for interactive API docs."}


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "dataset_latest_date": repo.latest_date(),
        "station_count": len(repo.list_stations()),
    }


# ---------------------------------------------------------------------------
# User Management Module (Week 1&2)
# ---------------------------------------------------------------------------
@app.post("/auth/login", response_model=Token, tags=["User Management"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return Token(access_token=token)


@app.get("/auth/me", response_model=UserProfile, tags=["User Management"])
def read_profile(current_user: UserProfile = Depends(get_current_user)):
    return current_user


@app.get("/admin/ping", tags=["User Management"])
def admin_only(current_user: UserProfile = Depends(require_admin)):
    return {"message": f"Welcome, {current_user.full_name}. Admin access confirmed."}


# ---------------------------------------------------------------------------
# Crowd Monitoring Module (Week 1&2) — now with real per-station capacity
# ---------------------------------------------------------------------------
@app.get("/stations", tags=["Crowd Monitoring"])
def get_stations(current_user: UserProfile = Depends(get_current_user)):
    return {"stations": repo.list_stations(), "count": len(repo.list_stations())}


@app.get("/crowd/live", tags=["Crowd Monitoring"])
def get_live_crowd(on_date: str = None, hour: int = 8, current_user: UserProfile = Depends(get_current_user)):
    on_date = on_date or repo.latest_date()
    return crowd_monitoring.get_live_snapshot(on_date, hour)


@app.get("/crowd/station/{station}", tags=["Crowd Monitoring"])
def get_station_snapshot(station: str, on_date: str = None, hour: int = 8,
                          current_user: UserProfile = Depends(get_current_user)):
    on_date = on_date or repo.latest_date()
    result = repo.station_snapshot(station, on_date, hour)
    if not result:
        raise HTTPException(status_code=404, detail="No data for this station/date/hour")
    return result


@app.get("/crowd/analytics/{station}", tags=["Crowd Monitoring"])
def get_station_analytics(station: str, days: int = 30, current_user: UserProfile = Depends(get_current_user)):
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return crowd_monitoring.get_station_analytics(station, days=days)


@app.get("/crowd/heatmap", tags=["Crowd Monitoring"])
def get_congestion_heatmap(on_date: str = None, current_user: UserProfile = Depends(get_current_user)):
    on_date = on_date or repo.latest_date()
    return crowd_monitoring.get_heatmap(on_date)


@app.get("/stations/capacity", tags=["Crowd Monitoring"])
def get_all_capacities(current_user: UserProfile = Depends(get_current_user)):
    """Real per-station hourly capacity reference table."""
    return repo.load_capacity()


# ---------------------------------------------------------------------------
# AI Prediction Module (Week 3&4)
# ---------------------------------------------------------------------------
@app.post("/ai/train", tags=["AI Prediction"])
def train_models(current_user: UserProfile = Depends(require_admin)):
    """(Re)trains the demand and delay forecasting models on the current dataset."""
    return ai_prediction.train_all_models()


@app.get("/ai/predict/demand/{station}", tags=["AI Prediction"])
def predict_demand(station: str, on_date: str, hour: int, current_user: UserProfile = Depends(get_current_user)):
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return ai_prediction.predict_demand(station, on_date, hour)


@app.get("/ai/predict/delay/{station}", tags=["AI Prediction"])
def predict_delay(station: str, on_date: str, hour: int, current_user: UserProfile = Depends(get_current_user)):
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return ai_prediction.predict_delay(station, on_date, hour)


@app.get("/ai/forecast/{station}", tags=["AI Prediction"])
def forecast_day(station: str, on_date: str, current_user: UserProfile = Depends(get_current_user)):
    """24-hour demand + delay forecast for a station (traffic pattern analysis)."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return {
        "station": station, "date": on_date,
        "demand_forecast": ai_prediction.forecast_peak_hours(station, on_date),
        "delay_forecast": ai_prediction.forecast_delays(station, on_date),
    }


@app.get("/ai/recommendations/{station}", tags=["AI Prediction"])
def get_recommendations(station: str, on_date: str, current_user: UserProfile = Depends(get_current_user)):
    """Smart recommendations combining demand + delay forecasts."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return {"station": station, "date": on_date, "recommendations": ai_prediction.smart_recommendations(station, on_date)}


# ---------------------------------------------------------------------------
# Scheduling Management Module (Week 3&4)
# ---------------------------------------------------------------------------
@app.get("/schedule/{station}", tags=["Scheduling"])
def get_schedule(station: str, on_date: str, current_user: UserProfile = Depends(get_current_user)):
    """Hour-by-hour recommended train frequency for a station."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return {"station": station, "date": on_date, "schedule": scheduling.recommended_schedule(station, on_date)}


@app.get("/schedule/{station}/peak-summary", tags=["Scheduling"])
def get_peak_summary(station: str, on_date: str, current_user: UserProfile = Depends(get_current_user)):
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return scheduling.peak_hour_summary(station, on_date)


@app.get("/schedule/{station}/delay-report", tags=["Scheduling"])
def get_delay_report(station: str, days: int = 90, current_user: UserProfile = Depends(get_current_user)):
    """Real delay-pattern report for a station (frequency, avg/max delay, worst hour)."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return scheduling.delay_report(station, days=days)


@app.get("/schedule/{station}/adjust-for-delay", tags=["Scheduling"])
def adjust_for_delay(station: str, on_date: str, hour: int, current_user: UserProfile = Depends(get_current_user)):
    """Delay-handling workflow: AI-predicted delay -> adjusted train frequency."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return scheduling.adjust_frequency_for_delay(station, on_date, hour)


# ---------------------------------------------------------------------------
# Alert & Notification Module (Week 5)
# ---------------------------------------------------------------------------
class EmergencyAnnouncementRequest(BaseModel):
    station: str
    message: str


@app.get("/alerts/overcrowding", tags=["Alerts"])
def get_overcrowding_alerts(on_date: str, hour: int, current_user: UserProfile = Depends(get_current_user)):
    """Live overcrowding alerts across all stations, using real per-station capacity."""
    return {"date": on_date, "hour": hour, "alerts": alerts.check_overcrowding_alerts(on_date, hour)}


@app.get("/alerts/forecasted/{station}", tags=["Alerts"])
def get_forecasted_alerts(station: str, on_date: str, current_user: UserProfile = Depends(get_current_user)):
    """Forward-looking overcrowding alerts from the AI demand forecast."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return {"station": station, "date": on_date, "alerts": alerts.check_forecasted_overcrowding_alerts(station, on_date)}


@app.get("/alerts/delays", tags=["Alerts"])
def get_delay_alerts(on_date: str, hour: int, current_user: UserProfile = Depends(get_current_user)):
    """Delay notifications from the real delay dataset for a given date/hour."""
    return {"date": on_date, "hour": hour, "alerts": alerts.check_delay_alerts(on_date, hour)}


@app.post("/alerts/emergency", tags=["Alerts"])
def post_emergency_announcement(
    body: EmergencyAnnouncementRequest, current_user: UserProfile = Depends(require_admin)
):
    """Broadcast an emergency announcement (admin only)."""
    try:
        return alerts.create_emergency_announcement(body.station, body.message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/alerts/live-feed", tags=["Alerts"])
def get_live_feed(on_date: str, hour: int, current_user: UserProfile = Depends(get_current_user)):
    """Combined real-time ticker: overcrowding + delay alerts, for the dashboard."""
    return alerts.real_time_feed(on_date, hour)


# ---------------------------------------------------------------------------
# Analytics Dashboard Module (Week 6 -- completes Milestone 3)
# ---------------------------------------------------------------------------
@app.get("/analytics/traffic", tags=["Analytics Dashboard"])
def get_traffic_report(days: int = 7, current_user: UserProfile = Depends(get_current_user)):
    """System-wide passenger traffic analytics: busiest/quietest stations over a window."""
    return analytics.system_traffic_report(days=days)


@app.get("/analytics/station/{station}", tags=["Analytics Dashboard"])
def get_station_performance(station: str, days: int = 30, current_user: UserProfile = Depends(get_current_user)):
    """Station performance report: crowd analytics + delay profile + AI insights combined."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return analytics.station_performance_report(station, days=days)


@app.get("/analytics/operational-summary", tags=["Analytics Dashboard"])
def get_operational_summary(on_date: str, hour: int, current_user: UserProfile = Depends(get_current_user)):
    """Live operational monitoring: system health, critical stations, active delays."""
    return analytics.operational_monitoring_summary(on_date, hour)


@app.get("/analytics/heatmap-report", tags=["Analytics Dashboard"])
def get_heatmap_report(on_date: str, current_user: UserProfile = Depends(get_current_user)):
    """Congestion heatmap + AI prediction insights: worst congestion points for the day."""
    return analytics.congestion_heatmap_report(on_date)


@app.get("/analytics/ai-insights/{station}", tags=["Analytics Dashboard"])
def get_ai_insights(station: str, on_date: str, current_user: UserProfile = Depends(get_current_user)):
    """Standalone AI prediction insights section: forecast curve + recommendations."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return analytics.ai_insights_report(station, on_date)
