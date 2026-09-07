from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str
    severity: str = "medium"
    station_id: Optional[str] = None
    train_id: Optional[str] = None
    title: str
    message: str


class AlertCreate(AlertBase):
    id: str


class AlertRead(AlertBase):
    id: str
    is_acknowledged: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None


class AlertBroadcast(BaseModel):
    type: str = "emergency"
    severity: str = "high"
    station_id: Optional[str] = None
    title: str
    message: str
