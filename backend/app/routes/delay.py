from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routes.auth import get_current_user
from app.services.delay_service import handle_delay

router = APIRouter(
    prefix="/api/delay",
    tags=["Delay Handling"]
)


class DelayRequest(BaseModel):
    delay_minutes: float
    scheduled_frequency: int = 10


@router.post("/analyze")
def delay_analysis(
    request: DelayRequest,
    current_user=Depends(get_current_user)
):
    return handle_delay(
        request.delay_minutes,
        request.scheduled_frequency
    )
