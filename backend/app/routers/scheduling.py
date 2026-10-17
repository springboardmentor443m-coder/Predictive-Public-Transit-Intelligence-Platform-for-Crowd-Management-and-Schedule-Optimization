
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth_utils import get_current_user
from app.database import get_db
from app.models.scheduling import FrequencyProposal, DelayRecord
from app.schemas.scheduling import (
    FrequencyProposalCreate,
    FrequencyProposalUpdate,
    DelayRecordCreate,
)
from app.services.scheduling_service import (
    get_metro_routes,
    get_route_stations,
    get_route_trips,
    get_trip_schedule,
    get_route_frequency,
    get_trip_frequency,
    get_trip_service,
    get_trip_service_dates,
    is_trip_active_on_date,
    station_belongs_to_route,
)
from app.services.scheduling_intelligence_service import (
    get_station_scheduling_recommendation,
    get_network_scheduling_recommendations,
)
from app.services.prediction_service import (
    predict_station_ridership_for_datetime,
)


router = APIRouter(prefix="/scheduling", tags=["Scheduling"])


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def _route_ids():
    """Extract route IDs from the existing GTFS route service."""
    routes_data = get_metro_routes()

    if isinstance(routes_data, dict):
        routes_data = routes_data.get(
            "routes",
            routes_data.get("data", []),
        )

    if not isinstance(routes_data, list):
        return set()

    route_ids = set()

    for route in routes_data:
        if not isinstance(route, dict):
            continue

        route_id = route.get("route_id")

        if route_id is not None:
            route_ids.add(str(route_id))

    return route_ids


def _validate_route(route_id: str):
    """Reject proposal or delay records for unknown GTFS routes."""
    if route_id not in _route_ids():
        raise HTTPException(
            status_code=400,
            detail="The selected route does not exist in the GTFS route list.",
        )


# ---------------------------------------------------------
# GTFS SCHEDULE ENDPOINTS
# ---------------------------------------------------------

@router.get("/routes")
def routes(current_user=Depends(get_current_user)):
    return get_metro_routes()


@router.get("/routes/{route_id}/stations")
def stations(
    route_id: str,
    current_user=Depends(get_current_user),
):
    _validate_route(route_id)
    return get_route_stations(route_id)


@router.get("/routes/{route_id}/trips")
def trips(
    route_id: str,
    current_user=Depends(get_current_user),
):
    _validate_route(route_id)
    return get_route_trips(route_id)


@router.get("/routes/{route_id}/frequency")
def route_frequency(
    route_id: str,
    current_user=Depends(get_current_user),
):
    _validate_route(route_id)
    return get_route_frequency(route_id)


@router.get("/trips/{trip_id}/schedule")
def trip_schedule(
    trip_id: str,
    current_user=Depends(get_current_user),
):
    return get_trip_schedule(trip_id)


@router.get("/trips/{trip_id}/frequency")
def trip_frequency(
    trip_id: str,
    current_user=Depends(get_current_user),
):
    return get_trip_frequency(trip_id)


@router.get("/trips/{trip_id}/service")
def trip_service(
    trip_id: str,
    current_user=Depends(get_current_user),
):
    return get_trip_service(trip_id)


@router.get("/trips/{trip_id}/service-dates")
def trip_service_dates(
    trip_id: str,
    current_user=Depends(get_current_user),
):
    return get_trip_service_dates(trip_id)


@router.get("/trips/{trip_id}/active-status")
def trip_active_status(
    trip_id: str,
    service_date: date = Query(...),
    current_user=Depends(get_current_user),
):
    return {
        "trip_id": trip_id,
        "service_date": service_date.isoformat(),
        "is_active": is_trip_active_on_date(
            trip_id,
            service_date.isoformat(),
        ),
    }


# Compatibility endpoint for clients requesting service dates.
# A trip ID is needed because the GTFS service operates at trip level.
@router.get("/service-dates")
def service_dates(
    trip_id: str = Query(..., min_length=1),
    current_user=Depends(get_current_user),
):
    return get_trip_service_dates(trip_id)


@router.get("/active-status")
def active_status(
    trip_id: str = Query(..., min_length=1),
    service_date: date = Query(...),
    current_user=Depends(get_current_user),
):
    return {
        "trip_id": trip_id,
        "service_date": service_date.isoformat(),
        "is_active": is_trip_active_on_date(
            trip_id,
            service_date.isoformat(),
        ),
    }


# ---------------------------------------------------------
# SCHEDULING INTELLIGENCE
# ---------------------------------------------------------

@router.get("/intelligence/stations/{station}")
def station_scheduling_intelligence(
    station: str,
    current_user=Depends(get_current_user),
):
    recommendation = get_station_scheduling_recommendation(
        station.strip()
    )

    if recommendation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No scheduling recommendation found for station "
                f"'{station}'."
            ),
        )

    return recommendation


@router.get("/intelligence/summary")
def scheduling_intelligence_summary(
    current_user=Depends(get_current_user),
):
    return get_network_scheduling_recommendations()


# ---------------------------------------------------------
# THEORETICAL FREQUENCY WHAT-IF CALCULATION
# ---------------------------------------------------------

@router.get("/frequency/what-if")
def frequency_what_if(
    current_headway_minutes: float = Query(gt=0, le=240),
    proposed_headway_minutes: float = Query(gt=0, le=240),
    current_user=Depends(get_current_user),
):
    current_services_per_hour = 60.0 / current_headway_minutes
    proposed_services_per_hour = 60.0 / proposed_headway_minutes

    frequency_change_percent = (
        (
            proposed_services_per_hour - current_services_per_hour
        )
        / current_services_per_hour
    ) * 100.0

    return {
        "current_headway_minutes": current_headway_minutes,
        "proposed_headway_minutes": proposed_headway_minutes,
        "current_services_per_hour": round(
            current_services_per_hour, 2
        ),
        "proposed_services_per_hour": round(
            proposed_services_per_hour, 2
        ),
        "frequency_change_percent": round(
            frequency_change_percent, 2
        ),
        "assessment_type": "theoretical_what_if_calculation",
        "notice": (
            "This is an arithmetic comparison of service frequencies. "
            "It does not predict passenger waiting times, crowd reduction, "
            "or operational feasibility, and it does not change actual service."
        ),
    }


# ---------------------------------------------------------
# ML-INFORMED FREQUENCY ANALYSIS
# ---------------------------------------------------------

@router.get("/frequency/analysis")
def frequency_analysis(
    station: str = Query(min_length=1, max_length=150),
    target_date: date = Query(
        ...,
        description="Forecast date in YYYY-MM-DD format",
    ),
    target_hour: int = Query(ge=0, le=23),
    current_headway_minutes: float = Query(gt=0, le=240),
    proposed_headway_minutes: float = Query(gt=0, le=240),
    current_user=Depends(get_current_user),
):
    """
    Combine the station ridership forecast, analytical scheduling
    recommendation, and theoretical frequency arithmetic.

    The forecast does not estimate the causal effect of changing headway.
    """

    try:
        forecast = predict_station_ridership_for_datetime(
            station=station.strip(),
            target_date=target_date.isoformat(),
            target_hour=target_hour,
        )

        recommendation = get_station_scheduling_recommendation(
            forecast["station"]
        )

        if recommendation is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No scheduling recommendation is available for station "
                    f"'{forecast['station']}'."
                ),
            )

        current_services_per_hour = 60.0 / current_headway_minutes
        proposed_services_per_hour = 60.0 / proposed_headway_minutes

        frequency_change_percent = (
            (
                proposed_services_per_hour - current_services_per_hour
            )
            / current_services_per_hour
        ) * 100.0

        return {
            "station": forecast["station"],
            "target_datetime": forecast["target_datetime"],
            "predicted_ridership": forecast["predicted_ridership"],
            "unit": forecast["unit"],
            "model": forecast["model"],
            "forecast_type": forecast["forecast_type"],
            "is_observed_count": forecast["is_observed_count"],
            "data_mode": forecast["data_mode"],
            "is_simulated_data": forecast["is_simulated_data"],
            "is_live_data": forecast["is_live_data"],
            "forecast_note": forecast["note"],
            "latest_station_observation": (
                forecast["latest_station_observation"]
            ),
            "forecast_steps": forecast["forecast_steps"],
            "scheduling_recommendation": recommendation,
            "current_headway_minutes": current_headway_minutes,
            "proposed_headway_minutes": proposed_headway_minutes,
            "current_services_per_hour": round(
                current_services_per_hour, 2
            ),
            "proposed_services_per_hour": round(
                proposed_services_per_hour, 2
            ),
            "frequency_change_percent": round(
                frequency_change_percent, 2
            ),
            "assessment_type": "ml_forecast_with_analytical_scheduling",
            "notice": (
                "Ridership is a model-generated estimate based on the "
                "available dataset. Scheduling priority is an analytical "
                "recommendation. Frequency figures are arithmetic comparisons; "
                "they do not predict crowd reduction, waiting times, or "
                "operational feasibility. No live operations are changed."
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------
# FREQUENCY PROPOSALS
# ---------------------------------------------------------

@router.post("/proposals")
def create_frequency_proposal(
    proposal: FrequencyProposalCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _validate_route(proposal.route_id)

    if proposal.station and not station_belongs_to_route(
        proposal.route_id,
        proposal.station.strip(),
    ):
        raise HTTPException(
            status_code=400,
            detail="The selected station does not belong to this route.",
        )

    record = FrequencyProposal(**proposal.model_dump())

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/proposals")
def get_frequency_proposals(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(FrequencyProposal)

    if status:
        query = query.filter(FrequencyProposal.status == status)

    return query.order_by(FrequencyProposal.id.desc()).all()


@router.patch("/proposals/{proposal_id}")
def update_frequency_proposal(
    proposal_id: int,
    update: FrequencyProposalUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    record = (
        db.query(FrequencyProposal)
        .filter(FrequencyProposal.id == proposal_id)
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Frequency proposal not found.",
        )

    allowed_statuses = {
        "Proposed",
        "Approved",
        "Rejected",
        "Completed",
    }

    if update.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of {sorted(allowed_statuses)}.",
        )

    record.status = update.status

    db.commit()
    db.refresh(record)

    return record


# ---------------------------------------------------------
# DELAY RECORDS
# ---------------------------------------------------------

@router.post("/delays")
def create_delay_record(
    delay: DelayRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _validate_route(delay.route_id)

    record = DelayRecord(**delay.model_dump())

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/delays")
def get_delay_records(
    route_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(DelayRecord)

    if route_id:
        query = query.filter(DelayRecord.route_id == route_id)

    return query.order_by(DelayRecord.id.desc()).all()
