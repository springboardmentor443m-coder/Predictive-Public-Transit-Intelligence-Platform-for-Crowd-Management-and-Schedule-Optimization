from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StationCreate(BaseModel):
    name: str
    location: str
    line: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: int = 5000
    is_interchange: bool = False


class StationResponse(BaseModel):
    id: int
    name: str
    location: str
    line: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    capacity: int
    is_interchange: bool

    class Config:
        from_attributes = True


class StationUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    line: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: Optional[int] = None
    is_interchange: Optional[bool] = None

    class Config:
        from_attributes = True