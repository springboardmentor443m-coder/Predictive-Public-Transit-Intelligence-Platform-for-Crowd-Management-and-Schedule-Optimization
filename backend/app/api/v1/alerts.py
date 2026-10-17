from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.alert_service import OperationalAlertService
from app.services.audit_service import AuditService
from app.schemas.alert import (
    OperationalAlertResponse,
    AlertSummaryResponse,
    AcknowledgeAlertRequest
)
from app.core.events import manager as ws_manager

router = APIRouter(prefix="/alerts", tags=["Alert & Notification Intelligence"])


@router.get("/active", response_model=List[OperationalAlertResponse])
def get_active_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, WARNING, HIGH, CRITICAL"),
    alert_type: Optional[str] = Query(None, description="Filter by type: OVERCROWDING, LIVE_DELAY, SERVICE_ALERT, NETWORK_IMPACT"),
    db: Session = Depends(get_db)
):
    """
    Returns active or acknowledged operational alerts derived from GTFS-RT & ML models.
    Returns an empty list if no active alert conditions exist.
    """
    OperationalAlertService.sync_alerts(db)
    return OperationalAlertService.get_active_alerts(db, severity=severity, alert_type=alert_type)


@router.get("/history", response_model=List[OperationalAlertResponse])
def get_alert_history(
    limit: int = Query(100, ge=1, le=1000, description="Max historical alert records"),
    db: Session = Depends(get_db)
):
    """Returns historical operational alert log including resolved events."""
    return OperationalAlertService.get_alert_history(db, limit=limit)


@router.get("/summary", response_model=AlertSummaryResponse)
def get_alert_summary(db: Session = Depends(get_db)):
    """Returns compact alert summary counts for operations dashboard KPI cards."""
    OperationalAlertService.sync_alerts(db)
    return OperationalAlertService.get_summary(db)


@router.post("/{alert_id}/acknowledge", response_model=OperationalAlertResponse)
def acknowledge_alert(
    alert_id: int,
    payload: Optional[AcknowledgeAlertRequest] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Allows an operator to acknowledge an operational alert.
    Does not claim to alter real-world railway state; flags alert as reviewed.
    """
    user_email = current_user.email if current_user else "operator@metroflow.ny"
    alert = OperationalAlertService.acknowledge_alert(db, alert_id=alert_id, user_email=user_email)
    
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found.")

    # Audit log entry
    AuditService.create_log(
        db,
        action="ALERT_ACKNOWLEDGED",
        actor_email=user_email,
        metadata={
            "alert_key": alert.alert_key,
            "title": alert.title,
            "note": payload.note if payload else None
        }
    )

    return alert
