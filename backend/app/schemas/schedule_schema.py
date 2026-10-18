from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.models import ScheduleStatus


class ScheduleBase(BaseModel):
    train_id: int
    line_name: str
    origin_station_id: int
    destination_station_id: int
    departure_time: datetime
    arrival_time: datetime
    headway_minutes: int
    status: ScheduleStatus = ScheduleStatus.SCHEDULED


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleResponse(ScheduleBase):
    id: int
    train_code: str
    origin_station_name: str
    destination_station_name: str
    recommended_headway: int
    delay_minutes: int = 0
    conflict_detected: bool = False
    conflict_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScheduleOverrideRequest(BaseModel):
    schedule_id: int
    new_headway_minutes: int
    new_departure_time: Optional[datetime] = None
    reason: str


class FrequencyOptimizationRecommendation(BaseModel):
    line_name: str
    segment_name: str
    current_headway_minutes: int
    recommended_headway_minutes: int
    additional_trains_needed: int
    reason: str
    crowd_density_percentage: float
    timestamp: datetime
