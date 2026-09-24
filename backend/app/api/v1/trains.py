from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.train import Train
from app.services.train_monitor import get_live_train, get_live_trains, upcoming_schedule

router = APIRouter(prefix="/trains", tags=["trains"])


@router.get("", response_model=list[dict])
async def list_trains(db: Session = Depends(get_db), _=Depends(require_roles())):
    """Train fleet registry: rolling stock assets (model, capacity, status)."""
    return [
        {
            "id": t.id,
            "code": t.code,
            "model": t.model,
            "capacity": t.capacity,
            "status": t.status,
        }
        for t in db.query(Train).all()
    ]


@router.get("/live", response_model=list[dict])
async def live_trains(db: Session = Depends(get_db), _=Depends(require_roles())):
    """Real-time telemetry for the entire fleet: position, status, ETA, load."""
    return get_live_trains(db)


@router.get("/live/{train_id}", response_model=dict)
async def live_train(train_id: str, db: Session = Depends(get_db), _=Depends(require_roles())):
    snap = get_live_train(db, train_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Train not found")
    return snap


@router.get("/{train_id}/schedule", response_model=list[dict])
async def train_schedule(
    train_id: str, limit: int = Query(50, le=100), db: Session = Depends(get_db), _=Depends(require_roles())
):
    """Upcoming timetable entries (future stops) for a single train."""
    if db.query(Train).filter(Train.id == train_id).first() is None:
        raise HTTPException(status_code=404, detail="Train not found")
    return upcoming_schedule(db, train_id, limit)