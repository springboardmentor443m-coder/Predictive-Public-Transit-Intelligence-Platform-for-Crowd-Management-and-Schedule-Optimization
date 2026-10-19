
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.database import Base


class FrequencyProposal(Base):
    """Stores proposed service-frequency adjustments for analysis."""

    __tablename__ = "frequency_proposals"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(String(100), nullable=False, index=True)
    station = Column(String(150), nullable=True, index=True)
    current_headway_minutes = Column(Float, nullable=False)
    proposed_headway_minutes = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="Proposed")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DelayRecord(Base):
    """Stores manually entered or demonstration train-delay records."""

    __tablename__ = "delay_records"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(String(100), nullable=False, index=True)
    trip_id = Column(String(100), nullable=True, index=True)
    station = Column(String(150), nullable=True, index=True)
    delay_minutes = Column(Float, nullable=False)
    source = Column(String(50), nullable=False, default="Manual")
    description = Column(Text, nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
