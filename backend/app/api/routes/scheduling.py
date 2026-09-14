from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.transit import Schedule, Ridership, Station
from app.schemas.schemas import ScheduleIn, ScheduleOut
from app.services.crowd import recommend_frequency, congestion_level
from app.core.deps import get_current_user, require_role

router = APIRouter(prefix="/api/schedules", tags=["scheduling"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ScheduleOut])
def list_schedules(line: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Schedule).order_by(Schedule.line, Schedule.departure)
    if line:
        q = q.filter(Schedule.line == line)
    return q.limit(500).all()


@router.post("", response_model=ScheduleOut)
def create_schedule(data: ScheduleIn, db: Session = Depends(get_db),
                    _: object = Depends(require_role("admin", "operator"))):
    s = Schedule(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.post("/{sid}/delay")
def report_delay(sid: int, delay_min: int = Query(10), db: Session = Depends(get_db),
                 _: object = Depends(require_role("admin", "operator"))):
    s = db.query(Schedule).filter(Schedule.id == sid).first()
    if not s:
        return {"error": "not found"}
    s.delay_min = delay_min
    s.status = "delayed" if delay_min > 0 else "ontime"
    db.commit()
    return {"id": s.id, "status": s.status, "delay_min": s.delay_min}


@router.get("/optimize")
def optimize(line: str | None = None, db: Session = Depends(get_db)):
    """Frequency recommendation per station from latest demand."""
    rows = db.query(Ridership).order_by(Ridership.timestamp.desc()).limit(3000).all()
    latest = {}
    for r in rows:
        if r.station_code not in latest:
            latest[r.station_code] = (r.entries or 0) + (r.exits or 0)
    stations = db.query(Station).all()
    if line:
        stations = [s for s in stations if s.line == line]
    recs = []
    for s in stations:
        total = latest.get(s.code, 0)
        rec = recommend_frequency(total, s.capacity_per_hour)
        recs.append({"station_code": s.code, "station_name": s.name, "line": s.line,
                     "predicted_demand_pax_hr": total, "congestion": congestion_level(total), **rec})
    return sorted(recs, key=lambda x: x["load_factor"], reverse=True)
