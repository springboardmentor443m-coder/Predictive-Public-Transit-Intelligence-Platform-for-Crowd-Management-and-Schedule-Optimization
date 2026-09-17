from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AlertResponse(BaseModel):
    """Response schema for operational alerts."""
    id: int = Field(..., description="Unique alert integer ID")
    station_code: Optional[str] = Field(None, description="Station code where the alert occurred")
    alert_type: str = Field(..., description="Type of alert: 'overcrowding' or 'delay'")
    severity: str = Field(..., description="Severity level: 'low', 'medium', 'high', or 'critical'")
    message: str = Field(..., description="Descriptive alert text")
    created_at: datetime = Field(..., description="Timestamp when the alert was triggered")
    resolved: bool = Field(..., description="Whether the alert has been resolved")

    model_config = ConfigDict(from_attributes=True)
