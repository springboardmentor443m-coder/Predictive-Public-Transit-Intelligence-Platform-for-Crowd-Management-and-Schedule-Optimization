from fastapi import APIRouter, Depends

from app.routes.auth import get_current_user
from app.services.heatmap_service import get_heatmap_data


router = APIRouter(
    prefix="/api/heatmap",
    tags=["Heatmap"]
)


@router.get("/data")
def heatmap_data(
    current_user=Depends(get_current_user),
):
    return get_heatmap_data()