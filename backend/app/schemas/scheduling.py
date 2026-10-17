
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class FrequencyProposalCreate(BaseModel):
    route_id: str = Field(min_length=1, max_length=100)
    station: Optional[str] = Field(default=None, max_length=150)
    current_headway_minutes: float = Field(gt=0, le=240)
    proposed_headway_minutes: float = Field(gt=0, le=240)
    reason: str = Field(min_length=1)


class FrequencyProposalUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=30)


class DelayRecordCreate(BaseModel):
    route_id: str = Field(min_length=1, max_length=100)
    trip_id: Optional[str] = Field(default=None, max_length=100)
    station: Optional[str] = Field(default=None, max_length=150)
    delay_minutes: float = Field(ge=0)
    source: str = Field(default="Manual", max_length=50)
    description: Optional[str] = None


class FrequencyProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: str
    station: Optional[str] = None
    current_headway_minutes: float
    proposed_headway_minutes: float
    reason: str
    status: str
