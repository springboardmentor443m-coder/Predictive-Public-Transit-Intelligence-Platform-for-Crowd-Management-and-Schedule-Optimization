from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    location = Column(String, nullable=False)
    line = Column(String, nullable=True)  # Purple Line / Green Line

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    capacity = Column(Integer, nullable=False, default=5000)
    is_interchange = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Station {self.name}>"