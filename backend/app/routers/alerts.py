from datetime import date

from fastapi import APIRouter, Depends, Query

from app.auth_utils import get_current_user
from app.services.alert_service import (
    generate_station_alerts,
    generate_network_alerts
)


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts & Notifications"]
)


@router.get("/summary")
def alert_summary(
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
    return generate_network_alerts(
        selected_date=date,
        selected_hour=hour
    )


@router.get("/stations/{station}")
def station_alerts(
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
    return generate_station_alerts(
        station=station,
        selected_date=date,
        selected_hour=hour
    )