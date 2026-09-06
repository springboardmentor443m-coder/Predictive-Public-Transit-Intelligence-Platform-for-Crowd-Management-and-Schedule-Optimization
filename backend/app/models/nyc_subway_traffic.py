from sqlalchemy import Column, BigInteger, String, Float, DateTime
from app.core.database import Base


class NYCSubwayTraffic(Base):
    __tablename__ = "nyc_subway_traffic"

    id = Column(BigInteger, primary_key=True, index=True)

    unique_id = Column(BigInteger)
    datetime = Column(DateTime)

    stop_name = Column(String)
    remote_unit = Column(String)
    line = Column(String)
    connecting_lines = Column(String)
    daytime_routes = Column(String)

    division = Column(String)
    structure = Column(String)
    borough = Column(String)
    neighborhood = Column(String)

    latitude = Column(Float)
    longitude = Column(Float)

    entries = Column(BigInteger)
    exits = Column(BigInteger)