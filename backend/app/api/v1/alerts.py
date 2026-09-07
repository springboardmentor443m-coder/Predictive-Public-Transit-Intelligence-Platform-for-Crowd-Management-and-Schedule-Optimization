from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.schemas.alert import AlertBroadcast
from app.services.alert_service import (
    _alert_to_dict,
    acknowledge_alert,
    broadcast_alert,
    list_alerts,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[dict])
async def get_alerts(acknowledged: bool = Query(None), limit: int = Query(100, le=500), db: Session = Depends(get_db), _=Depends(require_roles())):
    return [_alert_to_dict(a) for a in list_alerts(db, acknowledged, limit)]


@router.post("/{alert_id}/acknowledge")
async def ack(alert_id: str, db: Session = Depends(get_db), _=Depends(require_roles("admin", "operator"))):
    alert = acknowledge_alert(db, alert_id)
    return _alert_to_dict(alert)


@router.post("/broadcast")
async def broadcast(payload: AlertBroadcast, db: Session = Depends(get_db), _=Depends(require_roles("admin"))):
    alert = broadcast_alert(db, payload)
    return _alert_to_dict(alert)
