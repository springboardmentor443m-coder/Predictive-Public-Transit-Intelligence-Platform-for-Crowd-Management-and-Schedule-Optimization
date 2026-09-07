from sqlalchemy import Column, Float, Integer, String

from app.core.database import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(String, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    line = Column(String, index=True, nullable=False)
    zone = Column(String, nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    capacity_per_hour = Column(Integer, nullable=False, default=400)

    @property
    def occupancy_pct(self) -> float:
        return 0.0
