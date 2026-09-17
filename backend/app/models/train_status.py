from datetime import datetime, timezone
from sqlalchemy import Integer, String, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class TrainStatus(Base):
    __tablename__ = "train_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    line: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    occupancy_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_train_status_line_time", "line", "timestamp"),
    )
