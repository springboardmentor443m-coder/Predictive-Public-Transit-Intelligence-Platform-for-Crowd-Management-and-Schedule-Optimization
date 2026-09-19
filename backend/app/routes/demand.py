from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.demand_service import predict_demand
from app.routes.auth import get_current_user


router = APIRouter(
    prefix="/api/demand",
    tags=["Demand Forecasting"]
)


class DemandRequest(BaseModel):
    hour: int
    day_of_week: int
    day_of_year: int
    month: int
    lag_1: float
    lag_24: float
    lag_168: float


@router.post("/predict")
def demand_prediction(
    request: DemandRequest,
    current_user=Depends(get_current_user)
):
    return predict_demand(
        hour=request.hour,
        day_of_week=request.day_of_week,
        day_of_year=request.day_of_year,
        month=request.month,
        lag_1=request.lag_1,
        lag_24=request.lag_24,
        lag_168=request.lag_168
    )
