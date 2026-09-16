from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.schemas.crowd import CrowdIngestRequest
from app.services.crowd_service import (
    get_all_live_snapshots,
    get_heatmap,
    get_live_snapshot,
    get_station_history,
    ingest_crowd_record,
)

router = APIRouter(prefix="/crowd", tags=["crowd"])


@router.get("/live", response_model=list[dict])
async def live_crowd(db: Session = Depends(get_db), _=Depends(require_roles())):
    return get_all_live_snapshots(db)


@router.get("/live/{station_id}", response_model=dict)
async def live_station(station_id: str, db: Session = Depends(get_db), _=Depends(require_roles())):
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


@router.post("/ingest", response_model=dict)
async def ingest_crowd(
    payload: CrowdIngestRequest,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "operator")),
):
    """Sensor/gate ingest: persist a ridership record + refresh live snapshot.

    Enables real gate-counter / ticketing feeds to push density data
    (PRD Crowd Monitoring: ticketing + sensor datasets).
    """
    snap = ingest_crowd_record(
        db,
        station_id=payload.station_id,
        entries=payload.entries,
        exits=payload.exits,
        occupancy=payload.occupancy,
        timestamp=payload.timestamp,
    )
    if not snap:
        raise HTTPException(status_code=404, detail="Station not found")
    return snap
