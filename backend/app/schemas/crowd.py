from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LiveCrowdSnapshot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    station_id: str
    station_name: str
    line: str
    occupancy: int
    capacity: int
    occupancy_pct: float
    congestion_level: str
    inflow_rate: float
    outflow_rate: float
    last_updated: datetime


class StationHeatmapPoint(BaseModel):
    station_id: str
    station_name: str
    hour: int
    occupancy_pct: float
    congestion_level: str


class StationHistoryPoint(BaseModel):
    timestamp: datetime
    entries: int
    exits: int
    occupancy: int
    congestion_level: str
