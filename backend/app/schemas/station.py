from typing import Optional

from pydantic import BaseModel, ConfigDict


class StationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    line: str
    zone: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    capacity_per_hour: int = 400


class StationCreate(StationBase):
    id: str


class StationRead(StationBase):
    id: str
