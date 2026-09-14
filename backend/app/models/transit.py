from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.db.database import Base


class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True)
    name = Column(String(128), nullable=False)
    line = Column(String(32), default="1")
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    capacity_per_hour = Column(Integer, default=5000)


class Ridership(Base):
    """Hourly entry/exit record (mirrors NYC Subway Traffic schema)."""
    __tablename__ = "ridership"
    id = Column(Integer, primary_key=True)
    station_code = Column(String(32), index=True)
    timestamp = Column(DateTime, index=True)
    entries = Column(Integer, default=0)
    exits = Column(Integer, default=0)


class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    line = Column(String(32), index=True)
    station_code = Column(String(32), index=True)
    direction = Column(String(32), default="Northbound")
    departure = Column(String(16))  # HH:MM
    frequency_min = Column(Integer, default=8)
    status = Column(String(32), default="ontime")  # ontime | delayed | cancelled
    delay_min = Column(Integer, default=0)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(32))  # overcrowding | delay | emergency | info
    severity = Column(String(16), default="medium")  # low | medium | high | critical
    station_code = Column(String(32), nullable=True)
    message = Column(Text)
    created_at = Column(DateTime)
    acknowledged = Column(Integer, default=0)
