from datetime import date

from fastapi import APIRouter, Depends, Query

from app.auth_utils import get_current_user

from app.services.operations_service import (
    get_station_operations_summary,
    get_network_operations_summary
)


router = APIRouter(
    prefix="/operations",
    tags=["Operations Decision Support"]
)


@router.get("/summary")
def operations_summary(
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
    return get_network_operations_summary(
        selected_date=date,
        selected_hour=hour
    )


@router.get("/stations/{station}")
def station_operations(
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
    result = get_station_operations_summary(
        station=station,
        selected_date=date,
        selected_hour=hour
    )

    if result is None:
        return {
            "station": station,
            "message": (
                "Operations data not found for "
                "the selected station/date/hour."
            )
        }

    return result