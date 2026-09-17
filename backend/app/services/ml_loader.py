from datetime import datetime
import re
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.station import Station
from app.ml.model_loader import ml_model
from app.ml.delay_model_loader import delay_ml_model
from app.services.cache import cache_service


def predict_crowd_density(
    station_code: str,
    timestamp: datetime,
    db: Session
) -> Tuple[float, str, bool]:
    """
    Core prediction service:
    1. Validates station_code exists in the database (404 if not found).
    2. Queries Redis cache using predict:{station_code}:{hour}:{day_of_week}.
    3. On cache miss: runs ML model inference, writes to Redis with 5 min TTL.
    Returns: (predicted_density, congestion_label, was_cached)
    """
    # 1. Validate station existence
    station = db.execute(
        select(Station).where(Station.station_code == station_code)
    ).scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with code '{station_code}' does not exist in the network.",
        )

    hour = timestamp.hour
    day_of_week = timestamp.weekday()

    # 2. Check Redis cache
    cached_result = cache_service.get_prediction(station_code, hour, day_of_week)
    if cached_result:
        density, label = cached_result
        return density, label, True

    # 3. Model inference on cache miss
    density, label = ml_model.predict(station_code, timestamp)

    # 4. Cache the result with 5-minute (300s) TTL
    cache_service.set_prediction(
        station_code=station_code,
        hour=hour,
        day_of_week=day_of_week,
        predicted_density=density,
        congestion_label=label,
        ttl_seconds=300,
    )

    return density, label, False


def predict_train_delay(
    station_code: str,
    timestamp: datetime,
    db: Session,
    weather_condition: str = "Clear",
    temperature_C: float = 15.0,
    precipitation_mm: float = 0.0,
    is_holiday: int = 0,
    station_obj: Optional[Station] = None,
) -> Tuple[int, float]:
    """
    Predicts operational delay status (0/1) and delay probability score (0.0 to 1.0)
    for a given station and timestamp using the trained Random Forest delay classifier.

    Delay model trained on synthetic data anchored to real crowd patterns — ROC-AUC 0.7322.
    Not trained on real-world delay records.

    Returns:
      (has_delay: int, delay_probability: float)
    """
    # 1. Validate station existence if station object not provided
    station = station_obj
    if not station:
        station = db.execute(
            select(Station).where(Station.station_code == station_code.strip())
        ).scalar_one_or_none()

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with code '{station_code}' does not exist in the network.",
        )

    # 2. Extract line number (e.g., 'Line 2' -> 2)
    line_digits = re.findall(r"\d+", station.line or "2")
    line_num = int(line_digits[0]) if line_digits else 2

    # 3. Obtain real crowd density flow reference for this station
    density, _, _ = predict_crowd_density(
        station_code=station.station_code,
        timestamp=timestamp,
        db=db,
    )

    # 4. Run delay model inference
    has_delay, delay_probability = delay_ml_model.predict(
        station_code=station.station_code,
        line_num=line_num,
        timestamp=timestamp,
        latitude=station.latitude,
        longitude=station.longitude,
        weather_condition=weather_condition,
        temperature_C=temperature_C,
        precipitation_mm=precipitation_mm,
        real_flow_pattern_ref=density,
        is_holiday=is_holiday,
    )

    return has_delay, delay_probability

