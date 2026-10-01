from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth_utils import get_current_user
from app.services.prediction_service import (
    predict_next_hour_ridership,
    predict_from_latest_data
)


router = APIRouter(
    prefix="/prediction",
    tags=["AI Prediction"]
)


class CrowdPredictionRequest(BaseModel):
    station: str
    hour: int
    day_of_week: int
    day_of_month: int
    month: int
    is_weekend: int
    is_peak_hour: int
    ridership_entry: float
    ridership_exit: float
    net_flow: float
    previous_hour_ridership: float
    previous_day_ridership: float
    rolling_3h_avg: float
    previous_hour_exit: float
    previous_hour_net_flow: float


@router.post("/crowd")
def predict_crowd(
    request: CrowdPredictionRequest,
    current_user=Depends(get_current_user)
):
    prediction = predict_next_hour_ridership(
        station=request.station,
        hour=request.hour,
        day_of_week=request.day_of_week,
        day_of_month=request.day_of_month,
        month=request.month,
        is_weekend=request.is_weekend,
        is_peak_hour=request.is_peak_hour,
        ridership_entry=request.ridership_entry,
        ridership_exit=request.ridership_exit,
        net_flow=request.net_flow,
        previous_hour_ridership=request.previous_hour_ridership,
        previous_day_ridership=request.previous_day_ridership,
        rolling_3h_avg=request.rolling_3h_avg,
        previous_hour_exit=request.previous_hour_exit,
        previous_hour_net_flow=request.previous_hour_net_flow
    )

    return {
        "station": request.station,
        "prediction": round(prediction, 2),
        "prediction_target": "next_hour_ridership",
        "unit": "passengers"
    }



@router.get("/crowd/latest/{station}")
def predict_latest_crowd(
    station: str,
    current_user=Depends(get_current_user)
):
    result = predict_from_latest_data(station)

    if result is None:
        return {
            "station": station,
            "message": "Station data not found"
        }

    return {
    **result,
    "prediction_note": (
        "Prediction is based on the latest available "
        "historical BMRCL station data."
    )
}