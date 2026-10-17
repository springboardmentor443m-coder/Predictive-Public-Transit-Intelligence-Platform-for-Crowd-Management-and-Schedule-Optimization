
from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth_utils import get_current_user
from app.services.analytics_service import (
    get_analytics_overview,
    get_analytics_ridership_trends,
    get_ridership_anomalies,
    get_station_comparison,
    get_network_passenger_flow,
    get_analytics_hotspots,
    get_analytics_model_insights,
    get_analytics_heatmap,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


def _run_analytics(function, *args, **kwargs):
    """Convert expected analytics data errors into HTTP responses."""
    try:
        return function(*args, **kwargs)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Analytics data unavailable: {exc}",
        ) from exc
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics calculation failed: {exc}",
        ) from exc


@router.get("/overview")
def analytics_overview(
    current_user=Depends(get_current_user),
):
    return _run_analytics(get_analytics_overview)


@router.get("/trends")
def analytics_trends(
    current_user=Depends(get_current_user),
):
    return _run_analytics(get_analytics_ridership_trends)


@router.get("/anomalies")
def analytics_anomalies(
    limit: int = Query(default=100, ge=1, le=1000),
    current_user=Depends(get_current_user),
):
    return _run_analytics(get_ridership_anomalies, limit=limit)


@router.get("/stations")
def analytics_stations(
    limit: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    return _run_analytics(get_station_comparison, limit=limit)


@router.get("/passenger-flow")
def analytics_passenger_flow(
    current_user=Depends(get_current_user),
):
    return _run_analytics(get_network_passenger_flow)


@router.get("/hotspots")
def analytics_hotspots(
    limit: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    return _run_analytics(get_analytics_hotspots, limit=limit)


@router.get("/model-insights")
def analytics_model_insights(
    current_user=Depends(get_current_user),
):
    return _run_analytics(get_analytics_model_insights)



@router.get("/heatmap")
def analytics_heatmap(
    current_user=Depends(get_current_user),
):
    return _run_analytics(get_analytics_heatmap)