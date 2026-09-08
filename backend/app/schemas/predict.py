from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CrowdPredictionRequest(BaseModel):
    """Request payload for ML crowd density prediction."""
    station_code: str = Field(..., description="Unique station identifier code (e.g. '222' for Gangnam)")
    timestamp: datetime = Field(..., description="Target ISO 8601 timestamp to predict crowd density for")


class CrowdPredictionResponse(BaseModel):
    """Response payload containing predicted crowd density and congestion classification."""
    station_code: str = Field(..., description="Unique station identifier code")
    timestamp: datetime = Field(..., description="Timestamp for which prediction was made")
    predicted_density: float = Field(..., description="Predicted passenger crowd density index (passengers or normalized scale)")
    congestion_label: str = Field(..., description="Congestion category: 'low', 'medium', 'high', or 'critical'")
    cached: Optional[bool] = Field(False, description="Whether this prediction result was served from Redis cache")
