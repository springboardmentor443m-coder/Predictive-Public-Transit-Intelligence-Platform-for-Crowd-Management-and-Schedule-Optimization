from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, nullable=False)
    severity = Column(String, default="medium", nullable=False)
    station_id = Column(String, ForeignKey("stations.id"), nullable=True)
    train_id = Column(String, ForeignKey("trains.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    resolved_at = Column(DateTime, nullable=True)
