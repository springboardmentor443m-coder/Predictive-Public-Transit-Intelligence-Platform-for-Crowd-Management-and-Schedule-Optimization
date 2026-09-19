from fastapi import APIRouter, Depends

from app.routes.auth import get_current_user
from app.services.traffic_analysis_service import get_traffic_analysis

router = APIRouter(
    prefix="/api/traffic",
    tags=["Traffic Analysis"]
)


@router.get("/summary")
def traffic_summary(
    current_user=Depends(get_current_user)
):
    return {
        "traffic_analysis": get_traffic_analysis()
    }
