from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routes.auth import get_current_user
from app.services.schedule_optimization_service import optimize_schedule

router = APIRouter(
    prefix="/api/schedule",
    tags=["Schedule Optimization"]
)


class ScheduleRequest(BaseModel):
    avg_ridership: float
    current_frequency: int = 10


@router.post("/optimize")
def schedule_optimization(
    request: ScheduleRequest,
    current_user=Depends(get_current_user)
):
    return optimize_schedule(
        request.avg_ridership,
        request.current_frequency
    )
