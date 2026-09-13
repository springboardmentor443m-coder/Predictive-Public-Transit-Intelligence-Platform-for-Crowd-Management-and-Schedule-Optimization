from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DelayRequest(BaseModel):
    line: str
    from_station: str
    to_station: str
    stop_sequence: float = 1.0
    hour: Optional[int] = None
    weekday: Optional[int] = None
    scheduled_time: Optional[str] = None
    train_type: str = "NJ Transit"


class DelayPredictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    line: str
    from_station: str
    to_station: str
    delay_bucket: str
    probabilities: dict[str, float]
    predicted_delay_minutes: float


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
