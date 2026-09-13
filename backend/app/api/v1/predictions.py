from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.schemas.prediction import DelayPredictResponse, DelayRequest
from app.services.prediction_service import (
    forecast_demand,
    predict_crowd,
    predict_delay,
    smart_recommendations,
    traffic_patterns,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/crowd", response_model=list[dict])
async def crowd_prediction(station_id: str = Query(None), hours: int = Query(12, ge=1, le=48), db: Session = Depends(get_db), _=Depends(require_roles())):
    return predict_crowd(station_id, hours, db=db)


@router.get("/demand", response_model=list[dict])
async def demand_forecast(station_id: str = Query(None), hours: int = Query(12, ge=1, le=48), db: Session = Depends(get_db), _=Depends(require_roles())):
    return forecast_demand(station_id, hours, db=db)


@router.post("/delay", response_model=DelayPredictResponse)
async def delay_prediction(req: DelayRequest, _=Depends(require_roles())):
    return predict_delay(req)


@router.get("/recommendations", response_model=list[dict])
async def recommendations(db: Session = Depends(get_db), _=Depends(require_roles())):
    return smart_recommendations(db)


@router.get("/patterns", response_model=list[dict])
async def patterns(db: Session = Depends(get_db), _=Depends(require_roles())):
    return traffic_patterns(db)
