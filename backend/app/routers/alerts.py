from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertResponse
from app.core.dependencies import require_roles

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=List[AlertResponse],
    summary="List active and historic alerts",
    description="Retrieve operational alerts with optional filtering by severity, station code, or resolution status.",
)
def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity ('low', 'medium', 'high', 'critical')"),
    station_code: Optional[str] = Query(None, description="Filter by station code"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status (true / false)"),
    db: Session = Depends(get_db),
):
    query = select(Alert)

    if severity:
        query = query.where(Alert.severity == severity.strip().lower())

    if station_code:
        query = query.where(Alert.station_code == station_code.strip())

    if resolved is not None:
        query = query.where(Alert.resolved == resolved)

    query = query.order_by(Alert.resolved.asc(), Alert.created_at.desc())
    alerts = db.execute(query).scalars().all()
    return alerts


@router.post(
    "/resolve/{alert_id}",
    response_model=AlertResponse,
    summary="Resolve an alert (Admin/Operator only)",
    description="Marks a specific alert as resolved. Requires JWT token with 'admin' or 'operator' role.",
    responses={
        401: {"description": "Unauthenticated: Missing or invalid JWT bearer token"},
        403: {"description": "Forbidden: User does not hold 'admin' or 'operator' role"},
        404: {"description": "Alert ID not found in database"},
    }
)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "operator"])),
):
    alert = db.execute(
        select(Alert).where(Alert.id == alert_id)
    ).scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found.",
        )

    alert.resolved = True
    db.commit()
    db.refresh(alert)
    return alert
