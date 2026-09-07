from typing import List, Dict
from pydantic import BaseModel


class RidershipTrendPoint(BaseModel):
    time_label: str
    total_inflow: int
    total_outflow: int
    avg_density_pct: float


class LinePerformanceMetric(BaseModel):
    line_name: str
    active_trains: int
    on_time_performance_pct: float
    avg_delay_minutes: float
    total_daily_ridership: int
    peak_crowd_station: str


class AnalyticsSummary(BaseModel):
    total_daily_passengers: int
    overall_otp_percentage: float  # On-Time Performance %
    active_trains_count: int
    critical_incidents_today: int
    peak_rush_hour: str
    line_performances: List[LinePerformanceMetric]
    ridership_trends: List[RidershipTrendPoint]
