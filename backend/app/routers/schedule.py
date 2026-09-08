from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schedule import (
    ScheduleRecommendationResponse,
    DelayReportRequest,
    DelayImpactResponse,
)
from app.services.ml_loader import predict_crowd_density
from app.services.scheduling import recommend_frequency, handle_delay

router = APIRouter(prefix="/schedule", tags=["Scheduling"])


@router.get(
    "/recommend/{station_code}",
    response_model=ScheduleRecommendationResponse,
    summary="Get train frequency recommendation",
    description=(
        "Evaluates the current crowd density for the specified station code at the current server time "
        "and returns an explainable operational headway/frequency recommendation with urgency and reason."
    ),
    responses={
        404: {"description": "Station code not found in database"}
    }
)
def get_schedule_recommendation(
    station_code: str,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    density, label, _ = predict_crowd_density(
        station_code=station_code.strip(),
        timestamp=now,
        db=db,
    )

    rec_result = recommend_frequency(density, label)

    return ScheduleRecommendationResponse(
        station_code=station_code,
        current_density=density,
        congestion_label=label,
        recommended_action=rec_result["recommended_action"],
        urgency=rec_result["urgency"],
        reason=rec_result["reason"],
        calculated_at=now,
    )


@router.post(
    "/delay",
    response_model=DelayImpactResponse,
    status_code=status.HTTP_200_OK,
    summary="Log train delay and compute downstream propagation",
    description=(
        "Logs a delay event at a specific station, calculates downstream delay propagation "
        "with buffer decay across subsequent stations on the line, and records the telemetry in the database."
    ),
    responses={
        200: {"description": "Delay logged and downstream impact calculated"},
        404: {"description": "Station or line not found or station not belonging to specified line"},
    }
)
def report_delay(
    request: DelayReportRequest,
    db: Session = Depends(get_db),
):
    impact = handle_delay(
        db=db,
        line=request.line,
        station_code=request.station_code,
        delay_minutes=request.delay_minutes,
    )
    return impact
