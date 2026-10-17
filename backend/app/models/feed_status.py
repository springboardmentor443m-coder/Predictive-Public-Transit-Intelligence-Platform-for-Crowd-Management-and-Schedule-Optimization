import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.core.database import Base


class HealthStatus(str, enum.Enum):
    CONNECTING = "CONNECTING"
    LIVE = "LIVE"
    STALE = "STALE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"


class FeedStatusModel(Base):
    __tablename__ = "feed_status"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(100), nullable=False, index=True)
    feed_timestamp = Column(DateTime, nullable=True, index=True)
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    entity_count = Column(Integer, default=0, nullable=False)
    status = Column(Enum(HealthStatus), default=HealthStatus.LIVE, nullable=False, index=True)
    error_message = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<FeedStatus(provider='{self.provider_name}', status='{self.status}', latency={self.latency_ms}ms)>"
