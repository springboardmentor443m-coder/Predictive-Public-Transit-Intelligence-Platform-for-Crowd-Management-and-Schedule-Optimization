from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routes.auth import get_current_user
from app.services.recommendation_service import generate_recommendations

router = APIRouter(
    prefix="/api/recommendations",
    tags=["AI Recommendations"]
)


class RecommendationRequest(BaseModel):
    predicted_ridership: float
    traffic_level: str
    delay_minutes: float


@router.post("/generate")
def recommendations(
    request: RecommendationRequest,
    current_user=Depends(get_current_user)
):
    return generate_recommendations(
        request.predicted_ridership,
        request.traffic_level,
        request.delay_minutes
    )
