from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.services.analytics_service import (
    ai_insights,
    overview,
    station_performance,
    traffic_series,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=dict)
async def get_overview(db: Session = Depends(get_db), _=Depends(require_roles())):
    return overview(db)


@router.get("/traffic", response_model=list[dict])
async def get_traffic(
    hours: int = Query(24, ge=1, le=168),
    start_time: datetime | None = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_roles()),
):
    return traffic_series(db, hours, start_time=start_time)


@router.get("/station-performance", response_model=list[dict])
async def get_station_performance(
    limit: int = Query(15, le=50),
    hours: int = Query(0, ge=0, le=168),
    start_time: datetime | None = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_roles()),
):
    return station_performance(db, limit, hours=hours or None, start_time=start_time)


@router.get("/insights", response_model=dict)
async def get_ai_insights(db: Session = Depends(get_db), _=Depends(require_roles())):
    """Consolidated AI insight panel (PRD Analytics: AI prediction insights)."""
    return ai_insights(db)
