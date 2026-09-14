from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.transit import Alert
from app.schemas.schemas import AlertIn, AlertOut
from app.services.alerts import register_ws, unregister_ws, create_alert, broadcast
from app.core.deps import get_current_user, require_role

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return db.query(Alert).order_by(Alert.created_at.desc()).limit(100).all()


@router.post("", response_model=AlertOut)
async def post_alert(data: AlertIn, db: Session = Depends(get_db),
                     _: object = Depends(require_role("admin", "operator"))):
    from datetime import datetime
    a = Alert(type=data.type, severity=data.severity, station_code=data.station_code,
              message=data.message, created_at=datetime.utcnow(), acknowledged=0)
    db.add(a)
    db.commit()
    db.refresh(a)
    await broadcast({"event": "alert", "id": a.id, "type": a.type,
                     "severity": a.severity, "station_code": a.station_code, "message": a.message})
    return a


@router.post("/{aid}/ack")
def ack(aid: int, db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    a = db.query(Alert).filter(Alert.id == aid).first()
    if a:
        a.acknowledged = 1
        db.commit()
    return {"ok": True}


@router.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await ws.accept()
    register_ws(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        unregister_ws(ws)
