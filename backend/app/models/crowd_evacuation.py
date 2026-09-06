from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base


class CrowdEvacuation(Base):
    __tablename__ = "crowd_evacuation"

    id = Column(Integer, primary_key=True, index=True)

    scenario = Column(String)
    sensor_type = Column(String)
    evacuation_strategy_type = Column(String)
    route_status = Column(String)

    crowd_density = Column(Float)
    evacuation_time_seconds = Column(Float)
    success_rate_percent = Column(Float)