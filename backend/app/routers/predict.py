from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.predict import CrowdPredictionRequest, CrowdPredictionResponse
from app.services.ml_loader import predict_crowd_density

router = APIRouter(prefix="/predict", tags=["Prediction"])


@router.post(
    "/crowd",
    response_model=CrowdPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict crowd density and congestion level",
    description=(
        "Takes a station code and timestamp, checks Redis cache, passes derived temporal features "
        "(hour, day_of_week, is_weekend) through the trained ML model, and returns predicted crowd density and label."
    ),
    responses={
        404: {"description": "Station code not found in database"},
        422: {"description": "Validation error (invalid timestamp or malformed request payload)"},
    }
)
def predict_crowd(
    request: CrowdPredictionRequest,
    db: Session = Depends(get_db),
):
    density, label, cached = predict_crowd_density(
        station_code=request.station_code.strip(),
        timestamp=request.timestamp,
        db=db,
    )

    return CrowdPredictionResponse(
        station_code=request.station_code,
        timestamp=request.timestamp,
        predicted_density=density,
        congestion_label=label,
        cached=cached,
    )
