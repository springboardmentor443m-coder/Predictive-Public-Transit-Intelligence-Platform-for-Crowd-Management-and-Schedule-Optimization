from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PassengerTapEvent(BaseModel):
    event_id: str
    station_id: int
    station_code: str
    station_name: str
    line_name: str
    gate_id: str
    event_type: str  # "TAP_IN" | "TAP_OUT"
    card_token: str
    fare_category: str  # "STANDARD" | "STUDENT" | "SENIOR" | "COMMUTER_PASS"
    timestamp: datetime


class TrainCarLoad(BaseModel):
    car_id: str
    car_number: int
    passenger_count: int
    max_capacity: int = 250
    load_percentage: float
    crowd_level: str  # "SEATS_AVAILABLE" | "STANDING_ROOM" | "CROWDED" | "CRUSH_LOAD"


class TrainPassengerTelemetry(BaseModel):
    train_id: str
    train_code: str
    line_name: str
    current_station: str
    next_station: str
    eta_seconds: int
    total_passengers: int
    total_capacity: int = 1000
    overall_load_pct: float
    speed_kmh: float
    status: str  # "IN_TRANSIT" | "AT_STATION" | "BOARDING"
    cars: List[TrainCarLoad]
    last_updated: datetime


class StationPassengerMetric(BaseModel):
    station_id: int
    station_code: str
    station_name: str
    line_name: str
    tap_ins_last_minute: int
    tap_outs_last_minute: int
    net_flux: int
    current_platform_passengers: int
    crowd_status: str


class GtfsRtConfig(BaseModel):
    feed_url: str
    api_key: Optional[str] = None
    feed_type: str = "VEHICLE_POSITIONS"  # VEHICLE_POSITIONS | TRIP_UPDATES | CUSTOM_JSON
    provider_name: Optional[str] = "Custom GTFS-RT Feed"
    is_enabled: bool = True


class GtfsRtStatusResponse(BaseModel):
    is_active: bool
    feed_url: Optional[str] = None
    provider_name: str = "Simulated AFC/APC Stream"
    last_polled: Optional[datetime] = None
    status_message: str
    entities_ingested: int
    sample_entities: List[Dict[str, Any]] = []


class RealtimePassengerStreamResponse(BaseModel):
    timestamp: datetime
    system_inflow_ppm: int
    system_outflow_ppm: int
    net_passenger_flux: int
    total_active_passengers_in_transit: int
    recent_tap_events: List[PassengerTapEvent]
    trains: List[TrainPassengerTelemetry]
    station_metrics: List[StationPassengerMetric]
    gtfs_rt_status: GtfsRtStatusResponse
