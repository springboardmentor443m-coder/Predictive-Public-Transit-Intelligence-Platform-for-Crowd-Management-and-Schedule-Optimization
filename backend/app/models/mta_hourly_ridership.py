from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base


class MTAHourlyRidership(Base):
    __tablename__ = "mta_hourly_ridership"

    id = Column(Integer, primary_key=True, index=True)

    transit_timestamp = Column(DateTime)
    station_complex_id = Column(String)
    station_complex = Column(String)
    borough = Column(String)
    routes = Column(String)
    payment_method = Column(String)

    ridership = Column(Float)
    transfers = Column(Float)

    latitude = Column(Float)
    longitude = Column(Float)
    georeference = Column(String)