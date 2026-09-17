from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models.station import Station
from app.models.ridership import RidershipLog
from app.models.train_status import TrainStatus
from app.models.alert import Alert
from pydantic import BaseModel, ConfigDict

router = APIRouter(tags=["Stations & Analytics"])


class RidershipHistoryPoint(BaseModel):
    timestamp: datetime
    hour: int
    inflow: int
    outflow: int
    total_ridership: int
    is_weekend: bool


class StationHistoryResponse(BaseModel):
    station_code: str
    station_name: str
    line: str
    days: int
    history: List[RidershipHistoryPoint]


class StationRankingItem(BaseModel):
    station_code: str
    name_en: str
    name_kr: Optional[str] = None
    line: str
    district: Optional[str] = None
    total_inflow: int
    total_outflow: int
    total_traffic: int
    alert_count: int


class SystemAnalyticsResponse(BaseModel):
    total_stations: int
    total_lines: int
    total_alerts: int
    active_alerts: int
    average_network_occupancy: float
    busiest_stations: List[StationRankingItem]


@router.get(
    "/stations/{station_code}/history",
    response_model=StationHistoryResponse,
    summary="Get station historical ridership time-series",
    description="Returns hourly inflow and outflow logs for a station over the past N days for charting.",
    responses={404: {"description": "Station not found"}}
)
def get_station_history(
    station_code: str,
    days: int = Query(7, ge=1, le=30, description="Number of historical days to fetch"),
    db: Session = Depends(get_db),
):
    station = db.execute(
        select(Station).where(Station.station_code == station_code.strip())
    ).scalar_one_or_none()

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with code '{station_code}' not found.",
        )

    since = datetime.now(timezone.utc) - timedelta(days=days)

    records = db.execute(
        select(RidershipLog)
        .where(
            RidershipLog.station_code == station_code.strip(),
            RidershipLog.timestamp >= since,
        )
        .order_by(RidershipLog.timestamp.asc())
    ).scalars().all()

    history_points = [
        RidershipHistoryPoint(
            timestamp=r.timestamp,
            hour=r.hour,
            inflow=r.inflow,
            outflow=r.outflow,
            total_ridership=r.inflow + r.outflow,
            is_weekend=r.is_weekend,
        )
        for r in records
    ]

    return StationHistoryResponse(
        station_code=station.station_code,
        station_name=station.name_en,
        line=station.line,
        days=days,
        history=history_points,
    )


@router.get(
    "/analytics/overview",
    response_model=SystemAnalyticsResponse,
    summary="Get system-wide analytics and station performance rankings",
    description="Returns high-level network health metrics, busiest stations, and active delay statistics.",
)
def get_analytics_overview(
    limit: int = Query(10, ge=3, le=50, description="Top N stations to return"),
    db: Session = Depends(get_db),
):
    total_stations = db.execute(select(func.count(Station.station_code))).scalar() or 0
    total_lines = len(db.execute(select(Station.line).distinct()).scalars().all())
    total_alerts = db.execute(select(func.count(Alert.id))).scalar() or 0
    active_alerts = db.execute(select(func.count(Alert.id)).where(Alert.resolved == False)).scalar() or 0

    avg_occupancy = db.execute(select(func.avg(TrainStatus.occupancy_pct))).scalar() or 64.5

    # Top busiest stations by total inflow + outflow
    traffic_query = (
        select(
            Station.station_code,
            Station.name_en,
            Station.name_kr,
            Station.line,
            Station.district,
            func.sum(RidershipLog.inflow).label("sum_inflow"),
            func.sum(RidershipLog.outflow).label("sum_outflow"),
            (func.sum(RidershipLog.inflow) + func.sum(RidershipLog.outflow)).label("total_traffic"),
        )
        .join(RidershipLog, Station.station_code == RidershipLog.station_code)
        .group_by(Station.station_code)
        .order_by(desc("total_traffic"))
        .limit(limit)
    )

    results = db.execute(traffic_query).all()

    rankings: List[StationRankingItem] = []
    for r in results:
        # Count alerts for this station
        al_count = db.execute(
            select(func.count(Alert.id)).where(Alert.station_code == r.station_code)
        ).scalar() or 0

        rankings.append(
            StationRankingItem(
                station_code=r.station_code,
                name_en=r.name_en,
                name_kr=r.name_kr,
                line=r.line,
                district=r.district,
                total_inflow=int(r.sum_inflow or 0),
                total_outflow=int(r.sum_outflow or 0),
                total_traffic=int(r.total_traffic or 0),
                alert_count=al_count,
            )
        )

    return SystemAnalyticsResponse(
        total_stations=total_stations,
        total_lines=total_lines,
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        average_network_occupancy=round(float(avg_occupancy), 1),
        busiest_stations=rankings,
    )
