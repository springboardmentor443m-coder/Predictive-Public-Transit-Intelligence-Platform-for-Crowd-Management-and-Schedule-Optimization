from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from app.core.database import Base
from app.schemas.live_data import DataState


class AlertType(str, PyEnum):
    OVERCROWDING = "OVERCROWDING"
    LIVE_DELAY = "LIVE_DELAY"
    SERVICE_ALERT = "SERVICE_ALERT"
    NETWORK_IMPACT = "NETWORK_IMPACT"


class AlertSeverity(str, PyEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class OperationalAlertModel(Base):
    __tablename__ = "operational_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_key = Column(String(150), unique=True, index=True, nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    entity_id = Column(String(100), nullable=True, index=True)
    entity_name = Column(String(255), nullable=True)
    
    observed_value = Column(String(100), nullable=True)
    predicted_value = Column(String(100), nullable=True)
    threshold_info = Column(String(255), nullable=True)
    recommended_action = Column(Text, nullable=True)
    
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    data_state = Column(Enum(DataState), default=DataState.LIVE, nullable=False)

    def __repr__(self):
        return f"<OperationalAlert(key='{self.alert_key}', type='{self.alert_type}', severity='{self.severity}', status='{self.status}')>"
