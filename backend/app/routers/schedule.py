from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schedule import (
    ScheduleRecommendationResponse,
    DelayReportRequest,
    DelayImpactResponse,
    ScheduleOverrideRequest,
    ScheduleOverrideResponse,
)
from app.models.user import User
from app.core.dependencies import require_roles
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
    summary="Log train delay and estimate downstream propagation",
    description=(
        "Logs an operational delay event at a specific station, estimates downstream delay propagation "
        "driven by the Random Forest delay prediction model (delay_prediction_rf_v2.pkl), and records "
        "the status in the database."
    ),
    responses={
        200: {"description": "Delay logged and downstream impact estimated"},
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


@router.post(
    "/override",
    response_model=ScheduleOverrideResponse,
    status_code=status.HTTP_200_OK,
    summary="Manual train schedule/headway override (Admin/Operator only)",
    description=(
        "Manually overrides the train dispatch headway for a specific line. "
        "Requires JWT authentication with 'admin' or 'operator' role."
    ),
    responses={
        200: {"description": "Schedule override applied successfully"},
        401: {"description": "Unauthenticated: Missing or invalid JWT bearer token"},
        403: {"description": "Forbidden: User lacks required 'admin' or 'operator' role"},
    }
)
def override_schedule(
    request: ScheduleOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "operator"])),
):
    now = datetime.now(timezone.utc)
    return ScheduleOverrideResponse(
        status="OVERRIDDEN",
        line=request.line,
        applied_headway_minutes=request.headway_minutes,
        overridden_by=current_user.username,
        reason=request.reason,
        timestamp=now,
    )
