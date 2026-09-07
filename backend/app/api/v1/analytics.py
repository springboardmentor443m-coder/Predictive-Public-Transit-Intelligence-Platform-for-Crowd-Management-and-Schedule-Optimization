from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.services.analytics_service import (
    overview,
    station_performance,
    traffic_series,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=dict)
async def get_overview(db: Session = Depends(get_db), _=Depends(require_roles())):
    return overview(db)


@router.get("/traffic", response_model=list[dict])
async def get_traffic(hours: int = Query(24, ge=1, le=168), db: Session = Depends(get_db), _=Depends(require_roles())):
    return traffic_series(db, hours)


@router.get("/station-performance", response_model=list[dict])
async def get_station_performance(limit: int = Query(15, le=50), db: Session = Depends(get_db), _=Depends(require_roles())):
    return station_performance(db, limit)
