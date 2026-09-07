from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PredictionPoint(BaseModel):
    hour: int
    predicted_occupancy_pct: float
    lower: float
    upper: float
    congestion_level: str
    timestamp: Optional[datetime] = None


class DemandPoint(BaseModel):
    hour: int
    predicted_entries: int
    predicted_exits: int
    peak_probability: float


class Recommendation(BaseModel):
    station_id: str
    station_name: str
    current_headway_min: int
    recommended_headway_min: int
    reason: str
    capacity_utilization_pct: float
