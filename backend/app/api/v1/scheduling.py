import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.schedule import TrainSchedule
from app.schemas.schedule import ScheduleCreate, ScheduleRead
from app.services.scheduling_service import (
    apply_headway,
    handle_delay,
    list_schedules,
)

router = APIRouter(prefix="/scheduling", tags=["scheduling"])


@router.get("/schedules", response_model=list[ScheduleRead])
async def get_schedules(limit: int = Query(100, le=500), db: Session = Depends(get_db), _=Depends(require_roles())):
    return list_schedules(db, limit)


@router.post("/schedules", response_model=ScheduleRead)
async def create_schedule(s: ScheduleCreate, db: Session = Depends(get_db), operator=Depends(require_roles("admin", "operator"))):
    existing = db.query(TrainSchedule).filter(TrainSchedule.id == s.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Schedule already exists")
    sched = TrainSchedule(**s.model_dump())
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


@router.put("/schedules/{schedule_id}", response_model=ScheduleRead)
async def update_schedule(schedule_id: str, s: ScheduleCreate, db: Session = Depends(get_db), operator=Depends(require_roles("admin", "operator"))):
    sched = db.query(TrainSchedule).filter(TrainSchedule.id == schedule_id).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    for k, v in s.model_dump(exclude={"id"}).items():
        setattr(sched, k, v)
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str, db: Session = Depends(get_db), operator=Depends(require_roles("admin", "operator"))):
    sched = db.query(TrainSchedule).filter(TrainSchedule.id == schedule_id).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(sched)
    db.commit()
    return {"ok": True}


@router.get("/optimization", response_model=list[dict])
async def optimization(db: Session = Depends(get_db), _=Depends(require_roles())):
    from app.services.scheduling_service import get_optimization_recommendations
    return get_optimization_recommendations(db)


@router.post("/delay/{schedule_id}")
async def report_delay(schedule_id: str, delay_min: int = Body(..., embed=True), db: Session = Depends(get_db), operator=Depends(require_roles("admin", "operator"))):
    return handle_delay(db, schedule_id, delay_min)


@router.post("/apply-headway/{station_id}")
async def apply_frequency(station_id: str, headway_min: int | None = Body(None, embed=True), db: Session = Depends(get_db), operator=Depends(require_roles("admin", "operator"))):
    return apply_headway(db, station_id, headway_min)
