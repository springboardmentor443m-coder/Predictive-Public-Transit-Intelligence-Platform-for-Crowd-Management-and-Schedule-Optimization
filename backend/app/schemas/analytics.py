from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KpiStat(BaseModel):
    label: str
    value: str
    change: str | None = None
    trend: str | None = "neutral"


class TrafficSeriesPoint(BaseModel):
    hour: int
    passenger_k: float
    congestion_level: str


class StationPerformance(BaseModel):
    station_id: str
    station_name: str
    avg_occupancy_pct: float
    peak_occupancy_pct: float
    congestion_score: float
    entries_total: int
    exits_total: int
    punctuality_pct: float


class AnalyticsOverview(BaseModel):
    total_stations: int
    total_trains: int
    active_alerts: int
    current_overall_occupancy_pct: float
    avg_occupancy_pct: float
    on_time_pct: float
    predicted_peak_hour: int
