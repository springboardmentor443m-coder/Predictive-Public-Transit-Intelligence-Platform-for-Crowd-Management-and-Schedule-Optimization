from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base


class RidershipRecord(Base):
    __tablename__ = "ridership_records"

    id = Column(String, primary_key=True, index=True)
    station_id = Column(String, ForeignKey("stations.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.utcnow(), index=True)
    entries = Column(Integer, default=0)
    exits = Column(Integer, default=0)
    occupancy = Column(Integer, default=0)
    congestion_level = Column(String, default="low")

    station = None
