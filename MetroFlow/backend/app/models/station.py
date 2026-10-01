from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    location = Column(String, nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    capacity = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Station {self.name}>"