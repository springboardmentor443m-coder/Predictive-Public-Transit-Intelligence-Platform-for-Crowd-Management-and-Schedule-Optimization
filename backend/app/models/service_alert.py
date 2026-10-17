from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, JSON
from app.core.database import Base
from app.schemas.live_data import DataState


class ServiceAlertModel(Base):
    __tablename__ = "service_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(100), unique=True, index=True, nullable=False)
    header_text = Column(String(500), nullable=False)
    description_text = Column(Text, nullable=True)
    affected_routes = Column(JSON, nullable=True)  # List of route IDs
    affected_stops = Column(JSON, nullable=True)   # List of stop IDs
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    data_state = Column(Enum(DataState), default=DataState.LIVE, nullable=False)

    def __repr__(self):
        return f"<ServiceAlert(id='{self.alert_id}', header='{self.header_text[:30]}...')>"
