from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class RidershipLog(Base):
    __tablename__ = "ridership_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_code: Mapped[str] = mapped_column(
        String(32), ForeignKey("stations.station_code", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    hour: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 - 23
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    is_weekend: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    inflow: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outflow: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    station = relationship("Station", back_populates="ridership_logs")

    __table_args__ = (
        Index("idx_ridership_station_time", "station_code", "timestamp"),
        Index("idx_ridership_hour_dow", "hour", "day_of_week"),
    )
