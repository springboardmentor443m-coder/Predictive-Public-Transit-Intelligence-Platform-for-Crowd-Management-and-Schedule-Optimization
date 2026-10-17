from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.live_data import DataState
from app.models.feed_status import HealthStatus


class TransitVehicleState(BaseModel):
    vehicle_id: str
    trip_id: Optional[str] = None
    route_id: str
    direction_id: Optional[int] = None
    current_stop_id: Optional[str] = None
    current_stop_sequence: Optional[int] = None
    current_status: Optional[str] = None
    latitude: Optional[float] = Field(None, description="Strictly null if omitted by MTA live telemetry")
    longitude: Optional[float] = Field(None, description="Strictly null if omitted by MTA live telemetry")
    bearing: Optional[float] = None
    passenger_count: Optional[int] = Field(None, description="Null: Not provided by live MTA feed")
    occupancy_rate: Optional[float] = Field(None, description="Null: Not provided by live MTA feed")
    timestamp: datetime
    data_state: DataState = DataState.LIVE

    model_config = ConfigDict(from_attributes=True)


class NormalizedTripUpdate(BaseModel):
    trip_id: str
    route_id: str
    stop_id: str
    delay_seconds: int
    estimated_arrival: Optional[datetime] = None
    estimated_departure: Optional[datetime] = None
    timestamp: datetime
    data_state: DataState = DataState.LIVE

    model_config = ConfigDict(from_attributes=True)


class NormalizedServiceAlert(BaseModel):
    alert_id: str
    header_text: str
    description_text: Optional[str] = None
    affected_routes: List[str] = Field(default_factory=list)
    affected_stops: List[str] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active: bool = True
    timestamp: datetime
    data_state: DataState = DataState.LIVE

    model_config = ConfigDict(from_attributes=True)


class FeedHealthSummary(BaseModel):
    provider_name: str
    feed_timestamp: Optional[datetime] = None
    received_at: datetime
    latency_ms: int
    entity_count: int
    status: HealthStatus
    error_message: Optional[str] = None
    is_live: bool = True

    model_config = ConfigDict(from_attributes=True)
