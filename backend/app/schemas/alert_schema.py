from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class AlertItem(BaseModel):
    id: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    line_name: Optional[str] = None
    priority: str  # INFO, WARNING, CRITICAL
    category: str  # OVERCROWDING, TRAIN_DELAY, EMERGENCY_HALT, ANOMALY
    message: str
    timestamp: datetime
    is_resolved: bool = False


class PABroadcastRequest(BaseModel):
    station_ids: List[int]
    message: str
    priority: str = "WARNING"
    target_zone: str = "ALL_PLATFORMS"


class BroadcastResponse(BaseModel):
    broadcast_id: str
    status: str
    target_stations_count: int
    channels: List[str]  # PA_SYSTEM, SMS_GATEWAY, EMAIL_OPERATORS
    timestamp: datetime
