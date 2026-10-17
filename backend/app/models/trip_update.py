from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.core.database import Base
from app.schemas.live_data import DataState


class TripUpdateModel(Base):
    __tablename__ = "trip_updates"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(String(100), index=True, nullable=False)
    route_id = Column(String(50), index=True, nullable=False)
    stop_id = Column(String(50), index=True, nullable=False)
    delay_seconds = Column(Integer, default=0, nullable=False)
    estimated_arrival = Column(DateTime, nullable=True)
    estimated_departure = Column(DateTime, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    data_state = Column(Enum(DataState), default=DataState.LIVE, nullable=False)

    def __repr__(self):
        return f"<TripUpdate(trip='{self.trip_id}', stop='{self.stop_id}', delay={self.delay_seconds}s)>"
