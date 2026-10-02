from datetime import date

from fastapi import APIRouter, Depends, Query

from app.auth_utils import get_current_user
from app.services.monitoring_service import (
    get_network_monitoring,
    get_station_monitoring
)

router = APIRouter(
    prefix="/monitoring",
    tags=["Realtime Monitoring"]
)


@router.get("/summary")
def monitoring_summary(
    date: date | None = Query(
        default=None,
        description="Historical monitoring date, e.g. 2025-09-30"
    ),
    hour: int | None = Query(
        default=None,
        ge=0,
        le=23,
        description="Monitoring hour from 0 to 23"
    ),
    current_user=Depends(get_current_user)
):
    return get_network_monitoring(
        selected_date=date,
        selected_hour=hour
    )


@router.get("/stations/{station}")
def station_monitoring(
    station: str,
    date: date | None = Query(
        default=None,
        description="Historical monitoring date, e.g. 2025-09-30"
    ),
    hour: int | None = Query(
        default=None,
        ge=0,
        le=23,
        description="Monitoring hour from 0 to 23"
    ),
    current_user=Depends(get_current_user)
):
    result = get_station_monitoring(
        station=station,
        selected_date=date,
        selected_hour=hour
    )

    if result is None:
        return {
            "station": station,
            "message": "Monitoring data not found for the selected date/hour."
        }

    return result