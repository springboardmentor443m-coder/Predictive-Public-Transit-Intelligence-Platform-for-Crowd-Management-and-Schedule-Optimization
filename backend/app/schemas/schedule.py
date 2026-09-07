from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ScheduleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    train_id: str
    station_id: str
    direction: str
    arrival: datetime
    departure: datetime
    headway_min: int = 5
    status: str = "on_time"
    delay_min: int = 0
    is_peak: str = "no"


class ScheduleCreate(ScheduleBase):
    id: str


class ScheduleRead(ScheduleBase):
    id: str
