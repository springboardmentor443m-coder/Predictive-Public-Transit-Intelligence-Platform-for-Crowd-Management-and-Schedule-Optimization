from pydantic import BaseModel, ConfigDict
from typing import Optional


class StationBase(BaseModel):
    """Base station schema containing shared fields."""
    station_code: str
    name_en: str
    name_kr: Optional[str] = None
    line: str
    latitude: float
    longitude: float
    district: Optional[str] = None


class StationResponse(StationBase):
    """Response schema returned by station listing and detail endpoints."""
    model_config = ConfigDict(from_attributes=True)
