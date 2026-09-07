from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.services.crowd_service import (
    get_all_live_snapshots,
    get_heatmap,
    get_live_snapshot,
    get_station_history,
)

router = APIRouter(prefix="/crowd", tags=["crowd"])


@router.get("/live", response_model=list[dict])
async def live_crowd(db: Session = Depends(get_db), _=Depends(require_roles())):
    return get_all_live_snapshots(db)


@router.get("/live/{station_id}", response_model=dict)
async def live_station(station_id: str, db: Session = Depends(get_db), _=Depends(require_roles())):
    from fastapi import HTTPException
    snap = get_live_snapshot(db, station_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Station not found")
    return snap


@router.get("/heatmap", response_model=list[dict])
async def heatmap(db: Session = Depends(get_db), _=Depends(require_roles())):
    return get_heatmap(db)


@router.get("/station/{station_id}/history", response_model=list[dict])
async def station_history(station_id: str, hours: int = Query(24, ge=1, le=168), db: Session = Depends(get_db), _=Depends(require_roles())):
    return get_station_history(db, station_id, hours)
