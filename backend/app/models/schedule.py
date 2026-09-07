from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class TrainSchedule(Base):
    __tablename__ = "train_schedules"

    id = Column(String, primary_key=True, index=True)
    train_id = Column(String, ForeignKey("trains.id"), nullable=False, index=True)
    station_id = Column(String, ForeignKey("stations.id"), nullable=False, index=True)
    direction = Column(String, nullable=False)
    arrival = Column(DateTime, default=lambda: datetime.utcnow())
    departure = Column(DateTime, default=lambda: datetime.utcnow())
    headway_min = Column(Integer, nullable=False, default=5)
    status = Column(String, default="on_time", nullable=False)
    delay_min = Column(Integer, default=0, nullable=False)
    is_peak = Column(String, default="no", nullable=False)

    train = relationship("Train")
    station = relationship("Station")
