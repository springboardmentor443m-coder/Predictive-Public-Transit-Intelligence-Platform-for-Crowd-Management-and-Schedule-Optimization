from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routes.auth import get_current_user
from app.services.analytics_service import generate_analytics


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)


class AnalyticsRequest(BaseModel):
    total_passengers: int = 0
    active_alerts: int = 0
    delayed_trains: int = 0
    average_delay: float = 0
    peak_crowd_level: str = "normal"


@router.post("/summary")
def analytics_summary(
    request: AnalyticsRequest,
    current_user=Depends(get_current_user),
):
    return generate_analytics(
        total_passengers=request.total_passengers,
        active_alerts=request.active_alerts,
        delayed_trains=request.delayed_trains,
        average_delay=request.average_delay,
        peak_crowd_level=request.peak_crowd_level,
    )