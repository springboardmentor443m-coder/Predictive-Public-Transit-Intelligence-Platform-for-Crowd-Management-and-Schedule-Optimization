from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth_utils import get_current_user

from app.services.demand_forecasting_service import (
    predict_next_day_demand,
    predict_future_demand,
    predict_demand_for_date,
)

from app.services.prediction_service import (
    predict_next_hour_ridership,
    predict_from_latest_data,
    predict_station_ridership_for_datetime,
)

router = APIRouter(
    prefix="/prediction",
    tags=["AI Prediction"],
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
    current_user=Depends(get_current_user),
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
        previous_hour_net_flow=request.previous_hour_net_flow,
    )

    return {
        "station": request.station,
        "prediction": round(prediction, 2),
        "prediction_target": "next_hour_ridership",
        "unit": "passengers",
    }


@router.get("/crowd/latest/{station}")
def predict_latest_crowd(
    station: str,
    current_user=Depends(get_current_user),
):
    result = predict_from_latest_data(station)

    if result is None:
        return {
            "station": station,
            "message": "Station data not found",
        }

    # The service already includes a prediction_note that states whether the
    # dates are simulated/shifted demo dates. Return it unchanged instead of
    # overwriting it with a generic note.
    return result


@router.get("/demand")
def predict_demand(
    current_user=Depends(get_current_user),
):
    return predict_next_day_demand()


@router.get("/demand/forecast/{days}")
def predict_demand_forecast(
    days: int,
    current_user=Depends(get_current_user),
):
    if days not in (7, 30):
        raise HTTPException(
            status_code=400,
            detail="Supported forecast periods are 7 or 30 days.",
        )

    try:
        return predict_future_demand(days=days)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get("/demand/date/{target_date}")
def predict_demand_on_date(
    target_date: str,
    current_user=Depends(get_current_user),
):
    try:
        return predict_demand_for_date(target_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get("/crowd/forecast/{station}/{target_date}/{target_hour}")
def predict_future_hourly_crowd(
    station: str,
    target_date: str,
    target_hour: int,
    current_user=Depends(get_current_user),
):
    try:
        return predict_station_ridership_for_datetime(
            station=station,
            target_date=target_date,
            target_hour=target_hour,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
