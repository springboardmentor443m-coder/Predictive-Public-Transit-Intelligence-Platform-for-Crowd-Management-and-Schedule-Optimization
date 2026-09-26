from fastapi import APIRouter, Depends

from app.auth_utils import get_current_user
from app.services.crowd_service import (
    get_station_ridership,
    get_hourly_ridership,
    get_daily_ridership,
    get_peak_period_ridership
)

router = APIRouter(
    prefix="/crowd",
    tags=["Crowd Monitoring"]
)


@router.get("/stations")
def station_ridership(
    current_user=Depends(get_current_user)
):
    return {
        "stations": get_station_ridership()
    }


@router.get("/hourly")
def hourly_ridership(
    current_user=Depends(get_current_user)
):
    return {
        "hourly_ridership": get_hourly_ridership()
    }

@router.get("/daily")
def daily_ridership(
    current_user=Depends(get_current_user)
):
    return {
        "daily_ridership": get_daily_ridership()
    }


@router.get("/peak-periods")
def peak_period_ridership(
    current_user=Depends(get_current_user)
):
    return {
        "peak_periods": get_peak_period_ridership()
    }