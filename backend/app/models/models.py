from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class TrainStatus(str, enum.Enum):
    IN_TRANSIT = "IN_TRANSIT"
    AT_STATION = "AT_STATION"
    MAINTENANCE = "MAINTENANCE"
    HALTED = "HALTED"


class ScheduleStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    DELAYED = "DELAYED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.OPERATOR, nullable=False)
    assigned_station_id = Column(Integer, ForeignKey("stations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assigned_station = relationship("Station", back_populates="operators")


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    station_code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    line_name = Column(String(100), nullable=False, index=True)  # Red Line, Blue Line
    platform_capacity = Column(Integer, default=2000, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    sequence_order = Column(Integer, nullable=False)
    is_interchange = Column(Boolean, default=False)

    operators = relationship("User", back_populates="assigned_station")


class Train(Base):
    __tablename__ = "trains"

    id = Column(Integer, primary_key=True, index=True)
    train_code = Column(String(50), unique=True, index=True, nullable=False)
    line_name = Column(String(100), nullable=False)
    current_station_id = Column(Integer, ForeignKey("stations.id"), nullable=True)
    target_station_id = Column(Integer, ForeignKey("stations.id"), nullable=True)
    max_capacity = Column(Integer, default=1200, nullable=False)
    current_capacity = Column(Integer, default=0, nullable=False)
    status = Column(SQLEnum(TrainStatus), default=TrainStatus.IN_TRANSIT, nullable=False)
    speed_kmh = Column(Float, default=45.0)
    delay_minutes = Column(Integer, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"), nullable=False)
    line_name = Column(String(100), nullable=False)
    origin_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    destination_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    headway_minutes = Column(Integer, default=6)
    recommended_headway = Column(Integer, default=6)
    status = Column(SQLEnum(ScheduleStatus), default=ScheduleStatus.SCHEDULED, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    target = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
