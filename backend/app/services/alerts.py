from datetime import datetime
from sqlalchemy.orm import Session
from app.models.transit import Alert

_wss: set = set()


def register_ws(ws):
    _wss.add(ws)


def unregister_ws(ws):
    _wss.discard(ws)


async def broadcast(payload: dict):
    dead = []
    for ws in list(_wss):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for d in dead:
        _wss.discard(d)


def create_alert(db: Session, type: str, severity: str, message: str, station_code: str | None = None) -> Alert:
    a = Alert(type=type, severity=severity, station_code=station_code,
              message=message, created_at=datetime.utcnow(), acknowledged=0)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


async def check_and_raise(db: Session, station_code: str, total: float, level: str):
    if level in ("high", "critical"):
        msg = f"Overcrowding {level.upper()} at {station_code}: ~{int(total)} pax/hr"
        a = create_alert(db, "overcrowding", "critical" if level == "critical" else "high", msg, station_code)
        await broadcast({"event": "alert", "id": a.id, "type": a.type,
                         "severity": a.severity, "station_code": station_code, "message": msg})
        return a
    return None
