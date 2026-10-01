from pydantic import BaseModel


class StationCreate(BaseModel):
    name: str
    location: str
    latitude: float | None = None
    longitude: float | None = None
    capacity: int


class StationResponse(BaseModel):
    id: int
    name: str
    location: str
    latitude: float | None
    longitude: float | None
    capacity: int

class StationUpdate(BaseModel):
    name: str
    location: str
    latitude: float
    longitude: float
    capacity: int

    class Config:
        from_attributes = True