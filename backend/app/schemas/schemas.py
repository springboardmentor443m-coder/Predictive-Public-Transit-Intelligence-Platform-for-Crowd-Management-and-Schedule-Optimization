from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    full_name: str = ""
    password: str
    role: str = "operator"


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str = ""
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StationOut(BaseModel):
    code: str
    name: str
    line: str
    latitude: float
    longitude: float
    capacity_per_hour: int

    class Config:
        from_attributes = True


class CrowdPoint(BaseModel):
    station_code: str
    timestamp: datetime
    entries: int
    exits: int
    total: int
    congestion: str


class ScheduleIn(BaseModel):
    line: str
    station_code: str
    direction: str = "Northbound"
    departure: str
    frequency_min: int = 8
    status: str = "ontime"
    delay_min: int = 0


class ScheduleOut(ScheduleIn):
    id: int

    class Config:
        from_attributes = True


class AlertIn(BaseModel):
    type: str
    severity: str = "medium"
    station_code: str | None = None
    message: str


class AlertOut(AlertIn):
    id: int
    created_at: datetime | None = None
    acknowledged: int = 0

    class Config:
        from_attributes = True


class PredictionPoint(BaseModel):
    timestamp: datetime
    predicted_entries: float
    predicted_exits: float
    predicted_total: float
    congestion: str
