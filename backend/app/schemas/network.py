from pydantic import BaseModel


class NetworkStation(BaseModel):
    c: str
    n: str
    lat: float
    lng: float


class NetworkSegment(BaseModel):
    a: str
    b: str
    r: str


class NetworkPayload(BaseModel):
    stations: list[NetworkStation]
    segments: list[NetworkSegment]
    monitored: list[str]