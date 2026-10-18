from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class StationDensity(BaseModel):
    station_id: int
    station_code: str
    station_name: str
    line_name: str
    inflow_rate_ppm: int          # Passengers per minute
    outflow_rate_ppm: int         # Passengers per minute
    current_occupancy: int        # Net footfall
    platform_capacity: int
    density_percentage: float     # (Inflow - Outflow)/Capacity * 100
    status: str                   # NORMAL, MODERATE, CRITICAL
    latitude: float
    longitude: float
    is_interchange: bool
    last_updated: datetime


class HeatmapPoint(BaseModel):
    station_id: int
    name: str
    latitude: float
    longitude: float
    density_percentage: float
    status: str
    line_name: str


class CrowdSummaryResponse(BaseModel):
    total_system_occupancy: int
    average_density_percentage: float
    critical_stations_count: int
    moderate_stations_count: int
    normal_stations_count: int
    stations: List[StationDensity]
