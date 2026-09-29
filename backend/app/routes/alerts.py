
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routes.auth import get_current_user
from app.services.alert_service import generate_alerts

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


class AlertRequest(BaseModel):
    predicted_ridership: float = 0
    traffic_level: str = "normal"
    delay_minutes: float = 0


@router.post("/generate")
def create_alerts(
    request: AlertRequest,
    current_user=Depends(get_current_user),
):
    return generate_alerts(
        predicted_ridership=request.predicted_ridership,
        traffic_level=request.traffic_level,
        delay_minutes=request.delay_minutes,
    )