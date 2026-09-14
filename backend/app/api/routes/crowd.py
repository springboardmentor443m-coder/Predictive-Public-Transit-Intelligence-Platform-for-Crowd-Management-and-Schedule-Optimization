from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.transit import Station, Ridership
from app.schemas.schemas import StationOut
from app.services.crowd import congestion_level
from app.core.deps import get_current_user

router = APIRouter(prefix="/api", tags=["crowd"], dependencies=[Depends(get_current_user)])


@router.get("/stations", response_model=list[StationOut])
def stations(db: Session = Depends(get_db)):
    return db.query(Station).order_by(Station.code).all()


@router.get("/crowd/current")
def crowd_current(station_code: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Ridership).order_by(Ridership.timestamp.desc())
    if station_code:
        q = q.filter(Ridership.station_code == station_code)
    rows = q.limit(200).all()
    # latest per station
    seen, out = set(), []
    for r in rows:
        if r.station_code in seen:
            continue
        seen.add(r.station_code)
        total = (r.entries or 0) + (r.exits or 0)
        out.append({"station_code": r.station_code, "timestamp": r.timestamp,
                    "entries": r.entries, "exits": r.exits, "total": total,
                    "congestion": congestion_level(total)})
        if station_code:
            break
    return out


@router.get("/crowd/history")
def crowd_history(station_code: str, hours: int = Query(48, le=720), db: Session = Depends(get_db)):
    rows = (db.query(Ridership).filter(Ridership.station_code == station_code)
            .order_by(Ridership.timestamp.desc()).limit(hours).all())
    rows = sorted(rows, key=lambda r: r.timestamp)
    return [{"timestamp": r.timestamp, "entries": r.entries, "exits": r.exits,
             "total": (r.entries or 0) + (r.exits or 0),
             "congestion": congestion_level((r.entries or 0) + (r.exits or 0))} for r in rows]


@router.get("/crowd/heatmap")
def heatmap(db: Session = Depends(get_db)):
    """Latest total per station for heatmap rendering."""
    rows = db.query(Ridership).order_by(Ridership.timestamp.desc()).limit(2000).all()
    latest = {}
    for r in rows:
        if r.station_code not in latest:
            latest[r.station_code] = r
    stations = {s.code: s for s in db.query(Station).all()}
    out = []
    for code, r in latest.items():
        total = (r.entries or 0) + (r.exits or 0)
        s = stations.get(code)
        out.append({"station_code": code, "station_name": s.name if s else code,
                    "line": s.line if s else "?", "lat": s.latitude if s else 0,
                    "lon": s.longitude if s else 0, "total": total,
                    "congestion": congestion_level(total)})
    return sorted(out, key=lambda x: x["total"], reverse=True)


@router.get("/crowd/inflow-outflow")
def inflow_outflow(station_code: str, hours: int = Query(24, le=720), db: Session = Depends(get_db)):
    rows = (db.query(Ridership).filter(Ridership.station_code == station_code)
            .order_by(Ridership.timestamp.desc()).limit(hours).all())
    entries = sum(r.entries or 0 for r in rows)
    exits = sum(r.exits or 0 for r in rows)
    net = entries - exits
    return {"station_code": station_code, "window_hours": hours,
            "entries": entries, "exits": exits, "net_flow": net,
            "direction": "boarding-heavy" if net > 0 else ("alighting-heavy" if net < 0 else "balanced")}
