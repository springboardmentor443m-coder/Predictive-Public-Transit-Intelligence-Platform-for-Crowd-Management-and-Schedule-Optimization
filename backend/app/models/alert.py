from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_code: Mapped[Optional[str]] = mapped_column(
        String(32), ForeignKey("stations.station_code", ondelete="CASCADE"), nullable=True, index=True
    )
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False, default="overcrowding")  # "overcrowding" | "delay"
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")  # "low" | "medium" | "high" | "critical"
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    station = relationship("Station", back_populates="alerts")

    __table_args__ = (
        Index("idx_alert_severity_resolved", "severity", "resolved"),
    )
