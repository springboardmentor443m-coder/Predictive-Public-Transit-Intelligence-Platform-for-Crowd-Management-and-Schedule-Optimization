from datetime import datetime
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.station import Station
from app.ml.model_loader import ml_model
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
