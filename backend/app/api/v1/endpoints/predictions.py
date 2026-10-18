from typing import List
from fastapi import APIRouter, Query
from app.services.prediction_service import prediction_service
from app.schemas.prediction_schema import StationForecastResponse, CongestionAnomalyAlert

router = APIRouter()


@router.get("/forecast/{station_id}", response_model=StationForecastResponse)
async def get_station_forecast(
    station_id: int, 
    horizon: int = Query(30, description="Forecast horizon in minutes (15, 30, 60)")
):
    return await prediction_service.get_station_forecast(station_id, horizon)


@router.get("/all", response_model=List[StationForecastResponse])
async def get_all_forecasts(horizon: int = Query(30)):
    return await prediction_service.get_all_station_forecasts(horizon)


@router.get("/anomalies", response_model=List[CongestionAnomalyAlert])
async def get_congestion_anomalies():
    return await prediction_service.get_congestion_anomalies()
