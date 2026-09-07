from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class DemandForecastPoint(BaseModel):
    timestamp: str
    predicted_inflow: int
    predicted_outflow: int
    confidence_interval_lower: int
    confidence_interval_upper: int
    surge_probability: float


class StationForecastResponse(BaseModel):
    station_id: int
    station_name: str
    line_name: str
    forecast_horizon_minutes: int  # 15, 30, 60
    current_density_pct: float
    predicted_peak_density_pct: float
    risk_level: str  # LOW, MODERATE, HIGH, SEVERE
    surge_probability: float
    forecast_points: List[DemandForecastPoint]


class CongestionAnomalyAlert(BaseModel):
    station_id: int
    station_name: str
    line_name: str
    timestamp: str
    anomaly_score: float
    predicted_bottleneck_time: str
    suggested_action: str
