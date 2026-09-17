from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class ScheduleRecommendationResponse(BaseModel):
    """Response payload for train dispatch frequency recommendations."""
    station_code: str = Field(..., description="Target station identifier code")
    current_density: float = Field(..., description="Current predicted passenger crowd density (0-100 scale)")
    congestion_label: str = Field(..., description="Congestion category: 'low', 'medium', 'high', 'critical'")
    recommended_action: str = Field(..., description="Operational headway/dispatch action")
    urgency: str = Field(..., description="Action priority level: 'low', 'medium', 'high', 'critical'")
    reason: str = Field(..., description="Explainable reason explaining the automated scheduling decision")
    calculated_at: datetime = Field(..., description="Timestamp of calculation")


class DelayReportRequest(BaseModel):
    """Request payload for logging an operational delay incident."""
    line: str = Field(..., description="Transit line name (e.g. 'Line 2')")
    station_code: str = Field(..., description="Station code where the delay originated")
    delay_minutes: int = Field(..., ge=1, le=120, description="Observed delay duration in minutes")


class DownstreamAffectedStation(BaseModel):
    """Estimated delay propagation detail for a downstream station."""
    station_code: str = Field(..., description="Downstream station code")
    name_en: str = Field(..., description="Station name (English)")
    station_order: int = Field(..., description="Hops downstream from incident origin (1 = next station)")
    estimated_delay_minutes: float = Field(..., description="Projected remaining delay in minutes")
    estimated_eta_delay_seconds: int = Field(..., description="Projected ETA delay in seconds")


class DelayImpactResponse(BaseModel):
    """Response payload summarizing downstream delay impact and logged telemetry."""
    line: str = Field(..., description="Transit line")
    incident_station_code: str = Field(..., description="Station code where incident occurred")
    incident_station_name: str = Field(..., description="Station name where incident occurred")
    initial_delay_minutes: int = Field(..., description="Initial delay logged at origin station")
    logged_at: datetime = Field(..., description="Timestamp of delay event")
    affected_stations: List[DownstreamAffectedStation] = Field(..., description="List of downstream impacted stations")
