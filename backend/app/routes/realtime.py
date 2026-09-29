from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routes.auth import get_current_user
from app.services.realtime_service import get_realtime_update

router = APIRouter(
    prefix="/api/realtime",
    tags=["Real-Time Updates"]
)


class RealtimeRequest(BaseModel):
    station: str
    crowd_level: str = "normal"
    train_status: str = "on_time"
    delay_minutes: float = 0


@router.post("/update")
def realtime_update(
    request: RealtimeRequest,
    current_user=Depends(get_current_user),
):
    return get_realtime_update(
        station=request.station,
        crowd_level=request.crowd_level,
        train_status=request.train_status,
        delay_minutes=request.delay_minutes,
    )