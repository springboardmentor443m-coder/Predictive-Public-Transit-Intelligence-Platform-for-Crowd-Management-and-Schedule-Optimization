from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routes.auth import get_current_user
from app.services.announcement_service import create_announcement

router = APIRouter(
    prefix="/api/announcements",
    tags=["Emergency Announcements"]
)


class AnnouncementRequest(BaseModel):
    title: str
    message: str
    severity: str = "medium"
    station: str = "All Stations"


@router.post("/create")
def create_emergency_announcement(
    request: AnnouncementRequest,
    current_user=Depends(get_current_user),
):
    return create_announcement(
        title=request.title,
        message=request.message,
        severity=request.severity,
        station=request.station,
    )