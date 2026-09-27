from fastapi import APIRouter, Depends

from app.auth_utils import get_current_user
from app.services.scheduling_service import (
    get_metro_routes,
    get_route_stations
)


router = APIRouter(
    prefix="/scheduling",
    tags=["Scheduling"]
)


@router.get("/routes")
def metro_routes(
    current_user=Depends(get_current_user)
):
    return {
        "routes": get_metro_routes()
    }


@router.get("/routes/{route_id}/stations")
def route_stations(
    route_id: str,
    current_user=Depends(get_current_user)
):
    return {
        "route_id": route_id,
        "stations": get_route_stations(route_id)
    }