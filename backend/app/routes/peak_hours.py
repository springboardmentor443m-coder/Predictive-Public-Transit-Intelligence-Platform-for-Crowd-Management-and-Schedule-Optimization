from fastapi import APIRouter, Depends

from app.routes.auth import get_current_user
from app.services.peak_hour_service import get_peak_hours

router = APIRouter(
    prefix="/api/peak-hours",
    tags=["Peak Hour Detection"]
)


@router.get("/summary")
def peak_hours_summary(
    current_user=Depends(get_current_user)
):
    return {
        "peak_hours": get_peak_hours()
    }
