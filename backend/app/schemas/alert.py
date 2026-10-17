from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.alert import AlertType, AlertSeverity, AlertStatus
from app.schemas.live_data import DataState


class OperationalAlertResponse(BaseModel):
    id: int
    alert_key: str
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    observed_value: Optional[str] = None
    predicted_value: Optional[str] = None
    threshold_info: Optional[str] = None
    recommended_action: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    timestamp: datetime
    updated_at: datetime
    data_state: DataState

    model_config = ConfigDict(from_attributes=True)


class AlertSummaryResponse(BaseModel):
    total_active: int
    critical_count: int
    high_count: int
    warning_count: int
    info_count: int
    live_delays_count: int
    overcrowding_count: int
    service_alerts_count: int
    network_impact_count: int

    model_config = ConfigDict(from_attributes=True)


class AcknowledgeAlertRequest(BaseModel):
    note: Optional[str] = None
