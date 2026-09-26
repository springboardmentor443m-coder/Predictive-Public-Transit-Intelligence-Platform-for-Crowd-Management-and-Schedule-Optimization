from fastapi import APIRouter, Depends

from app.auth_utils import get_current_user
from app.services.crowd_service import get_station_ridership


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