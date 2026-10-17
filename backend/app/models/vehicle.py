from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from app.core.database import Base
from app.schemas.live_data import DataState


class TransitVehicle(Base):
    __tablename__ = "transit_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String(100), index=True, nullable=False)
    trip_id = Column(String(100), index=True, nullable=True)
    route_id = Column(String(50), index=True, nullable=False)
    direction_id = Column(Integer, nullable=True)
    current_stop_id = Column(String(50), index=True, nullable=True)
    current_stop_sequence = Column(Integer, nullable=True)
    current_status = Column(String(50), nullable=True)  # e.g., IN_TRANSIT_TO, STOPPED_AT, INCOMING_AT
    latitude = Column(Float, nullable=True)  # Strictly null if not provided by feed
    longitude = Column(Float, nullable=True)
    bearing = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    data_state = Column(Enum(DataState), default=DataState.LIVE, nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<TransitVehicle(id={self.id}, vehicle='{self.vehicle_id}', route='{self.route_id}')>"
