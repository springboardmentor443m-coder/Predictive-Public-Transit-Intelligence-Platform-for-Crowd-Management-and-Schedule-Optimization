"""
MetroFlow - AI Platform for Metro Crowd Management and Scheduling
Milestone 1 (Week 1 & 2): Project Initialization, Design Process & Core Setup

Scope delivered this milestone:
  - Auth + role-based access control (User Management Module)
  - Crowd monitoring dashboard (Crowd Monitoring Module)
  - Congestion tracking features

Run with:
  uvicorn app.main:app --reload --port 8000
Then open http://127.0.0.1:8000/docs for interactive API docs.
"""
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import (
    Token,
    UserProfile,
    authenticate_user,
    create_access_token,
    get_current_user,
    require_admin,
)
from app.data import repository as repo
from app.services import crowd_monitoring

app = FastAPI(
    title="MetroFlow API",
    description="AI Platform for Metro Crowd Management and Scheduling ",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["System"])
def root():
    return {"message": "MetroFlow API is running. Visit /docs for interactive API docs."}

# ---------------------------------------------------------------------------
# User Management Module (Admin/operator login, RBAC, profile)
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
# Crowd Monitoring Module
# ---------------------------------------------------------------------------
@app.get("/stations", tags=["Crowd Monitoring"])
def get_stations(current_user: UserProfile = Depends(get_current_user)):
    return {"stations": repo.list_stations(), "count": len(repo.list_stations())}


@app.get("/crowd/live", tags=["Crowd Monitoring"])
def get_live_crowd(
    on_date: str = None,
    hour: int = 8,
    current_user: UserProfile = Depends(get_current_user),
):
    """Live passenger density + congestion status across all stations for a given date/hour."""
    on_date = on_date or repo.latest_date()
    return crowd_monitoring.get_live_snapshot(on_date, hour)


@app.get("/crowd/station/{station}", tags=["Crowd Monitoring"])
def get_station_snapshot(
    station: str,
    on_date: str = None,
    hour: int = 8,
    current_user: UserProfile = Depends(get_current_user),
):
    on_date = on_date or repo.latest_date()
    result = repo.station_snapshot(station, on_date, hour)
    if not result:
        raise HTTPException(status_code=404, detail="No data for this station/date/hour")
    return result


@app.get("/crowd/analytics/{station}", tags=["Crowd Monitoring"])
def get_station_analytics(
    station: str,
    days: int = 30,
    current_user: UserProfile = Depends(get_current_user),
):
    """Station-wise analytics: avg daily entries/exits, peak hour, inflow/outflow balance."""
    if station not in repo.list_stations():
        raise HTTPException(status_code=404, detail="Unknown station")
    return crowd_monitoring.get_station_analytics(station, days=days)


@app.get("/crowd/heatmap", tags=["Crowd Monitoring"])
def get_congestion_heatmap(
    on_date: str = None,
    current_user: UserProfile = Depends(get_current_user),
):
    """Station x Hour congestion heatmap matrix for congestion tracking."""
    on_date = on_date or repo.latest_date()
    return crowd_monitoring.get_heatmap(on_date)


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "dataset_latest_date": repo.latest_date(),
        "station_count": len(repo.list_stations()),
    }
