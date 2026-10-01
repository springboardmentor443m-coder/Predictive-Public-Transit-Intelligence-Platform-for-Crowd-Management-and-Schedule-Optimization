from fastapi import APIRouter, Depends

from app.auth_utils import get_current_user
from app.services.scheduling_service import (
    get_metro_routes,
    get_route_stations,
    get_route_trips,
    get_trip_schedule,
    get_trip_frequency,
    get_route_frequency,
    get_trip_service,
    get_trip_service_dates,
    is_trip_active_on_date
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


@router.get("/routes/{route_id}/trips")
def route_trips(
    route_id: str,
    current_user=Depends(get_current_user)
):
    return {
        "route_id": route_id,
        "trips": get_route_trips(route_id)
    }



@router.get("/trips/{trip_id}/schedule")
def trip_schedule(
    trip_id: str,
    current_user=Depends(get_current_user)
):
    return {
        "trip_id": trip_id,
        "schedule": get_trip_schedule(trip_id)
    }



@router.get("/trips/{trip_id}/frequency")
def trip_frequency(
    trip_id: str,
    current_user=Depends(get_current_user)
):
    return {
        "trip_id": trip_id,
        "frequency": get_trip_frequency(trip_id)
    }


@router.get("/routes/{route_id}/frequency")
def route_frequency(
    route_id: str,
    current_user=Depends(get_current_user)
):
    return {
        "route_id": route_id,
        "frequency": get_route_frequency(route_id)
    }



@router.get("/trips/{trip_id}/service")
def trip_service(
    trip_id: str,
    current_user=Depends(get_current_user)
):
    return {
        "trip_id": trip_id,
        "service": get_trip_service(trip_id)
    }





@router.get("/trips/{trip_id}/service-dates")
def trip_service_dates(
    trip_id: str,
    current_user=Depends(get_current_user)
):
    return {
        "trip_id": trip_id,
        "service": get_trip_service_dates(trip_id)
    }




@router.get("/trips/{trip_id}/active")
def trip_active_on_date(
    trip_id: str,
    date: str,
    current_user=Depends(get_current_user)
):
    return {
        "trip_id": trip_id,
        "date": date,
        "active": is_trip_active_on_date(
            trip_id,
            date
        )
    }