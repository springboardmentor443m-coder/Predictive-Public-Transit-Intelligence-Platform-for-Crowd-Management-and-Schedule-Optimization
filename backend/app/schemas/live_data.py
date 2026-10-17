import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DataState(str, enum.Enum):
    LIVE = "LIVE"
    HISTORICAL = "HISTORICAL"
    PREDICTED = "PREDICTED"
    UNAVAILABLE = "UNAVAILABLE"


class VehiclePosition(BaseModel):
    vehicle_id: str
    trip_id: Optional[str] = None
    route_id: Optional[str] = None
    latitude: float
    longitude: float
    bearing: Optional[float] = None
    speed_kmh: Optional[float] = None
    current_stop_sequence: Optional[int] = None
    timestamp: datetime
    data_state: DataState = Field(..., description="Must explicitly define data state (LIVE, HISTORICAL, PREDICTED, UNAVAILABLE)")


class ServiceAlert(BaseModel):
    alert_id: str
    header_text: str
    description_text: Optional[str] = None
    cause: Optional[str] = None
    effect: Optional[str] = None
    affected_routes: List[str] = Field(default_factory=list)
    affected_stations: List[str] = Field(default_factory=list)
    timestamp: datetime
    data_state: DataState = Field(..., description="Must explicitly define data state")


class TripUpdate(BaseModel):
    trip_id: str
    route_id: str
    delay_seconds: int
    stop_sequence: Optional[int] = None
    next_station_id: Optional[str] = None
    timestamp: datetime
    data_state: DataState = Field(..., description="Must explicitly define data state")


class LiveFeedStatus(BaseModel):
    provider_name: str
    is_connected: bool
    data_state: DataState
    status_message: str
    last_sync: Optional[datetime] = None
