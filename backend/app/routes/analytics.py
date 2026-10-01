from fastapi import APIRouter, Query
from typing import Optional
from app.services.analytics import (
    get_live_ridership,
    get_station_list,
    get_station_hourly_avg,
    get_station_daily_trend,
    get_station_weekday_pattern,
    get_network_daily_summary,
    get_network_hourly_profile,
    get_top_stations,
    get_heatmap_data,
    predict_next_hours,
    get_peak_analysis,
    get_anomaly_stations,
    get_ai_insights,
    get_line_comparison,
    get_crowd_forecast_summary,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── Live Data ──────────────────────────────────────────────────────────────
@router.get("/live")
def live_ridership():
    """Real-time (simulated) ridership across all stations."""
    return {"data": get_live_ridership()}


# ── Station Level ──────────────────────────────────────────────────────────
@router.get("/stations/list")
def station_list():
    return {"stations": get_station_list()}


@router.get("/stations/{station}/hourly")
def station_hourly(station: str):
    return {"station": station, "data": get_station_hourly_avg(station)}


@router.get("/stations/{station}/daily")
def station_daily(station: str):
    return {"station": station, "data": get_station_daily_trend(station)}


@router.get("/stations/{station}/weekday")
def station_weekday(station: str):
    return {"station": station, "data": get_station_weekday_pattern(station)}


@router.get("/stations/{station}/predict")
def station_predict(station: str, hours: int = Query(default=6, ge=1, le=24)):
    return {"station": station, "predictions": predict_next_hours(station, hours)}


# ── Network Level ──────────────────────────────────────────────────────────
@router.get("/network/daily")
def network_daily():
    return {"data": get_network_daily_summary()}


@router.get("/network/hourly")
def network_hourly():
    return {"data": get_network_hourly_profile()}


@router.get("/network/top-stations")
def top_stations(n: int = Query(default=10, ge=1, le=84), hour: Optional[int] = None):
    return {"data": get_top_stations(n, hour)}


@router.get("/network/heatmap")
def heatmap():
    return {"data": get_heatmap_data()}


@router.get("/network/line-comparison")
def line_comparison():
    return {"data": get_line_comparison()}


# ── AI Intelligence ────────────────────────────────────────────────────────
@router.get("/ai/peak-analysis")
def peak_analysis():
    return get_peak_analysis()


@router.get("/ai/anomalies")
def anomalies(date: Optional[str] = None):
    return {"anomalies": get_anomaly_stations(date)}


@router.get("/ai/insights")
def ai_insights():
    return {"insights": get_ai_insights()}


@router.get("/ai/forecast")
def crowd_forecast():
    return get_crowd_forecast_summary()
