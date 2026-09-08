from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.db.base import Base


class Station(Base):
    __tablename__ = "stations"

    station_code: Mapped[str] = mapped_column(String(32), primary_key=True, index=True)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name_kr: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    line: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    ridership_logs: Mapped[List["RidershipLog"]] = relationship(
        "RidershipLog", back_populates="station", cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert", back_populates="station", cascade="all, delete-orphan"
    )
