from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_operator_or_admin
from app.models.vehicle import TransitVehicle
from app.models.trip_update import TripUpdateModel
from app.models.service_alert import ServiceAlertModel
from app.models.feed_status import FeedStatusModel, HealthStatus
from app.schemas.live_mta import TransitVehicleState, NormalizedTripUpdate, NormalizedServiceAlert, FeedHealthSummary
from app.services.live_data.ingestion import mta_provider, ingestion_service

router = APIRouter(dependencies=[Depends(require_operator_or_admin)])


@router.get("/live/health", response_model=FeedHealthSummary, summary="Get Live Feed Health & Staleness")
def get_live_feed_health(db: Session = Depends(get_db)):
    """Retrieve real-time MTA feed health status, staleness indicator, and processing latency."""
    latest_status = db.query(FeedStatusModel).order_by(FeedStatusModel.received_at.desc()).first()
    
    if not latest_status:
        # Fallback to provider status if DB has no historical records yet
        provider_status = mta_provider.get_status()
        return FeedHealthSummary(
            provider_name=mta_provider.provider_name,
            feed_timestamp=mta_provider.last_feed_timestamp,
            received_at=provider_status.last_sync or mta_provider.last_sync_time,
            latency_ms=mta_provider.last_latency_ms,
            entity_count=0,
            status=mta_provider.last_status,
            error_message=mta_provider.last_error,
            is_live=(mta_provider.last_status == HealthStatus.LIVE)
        )

    return FeedHealthSummary(
        provider_name=latest_status.provider_name,
        feed_timestamp=latest_status.feed_timestamp,
        received_at=latest_status.received_at,
        latency_ms=latest_status.latency_ms,
        entity_count=latest_status.entity_count,
        status=latest_status.status,
        error_message=latest_status.error_message,
        is_live=(latest_status.status == HealthStatus.LIVE)
    )


@router.get("/live/vehicles", response_model=List[TransitVehicleState], summary="List Active Live Metro Vehicles")
def get_live_vehicles(
    route_id: Optional[str] = Query(None, description="Filter by Subway Line Route ID (e.g. A, 1, L, N)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve current operational metro train states from the live MTA feed."""
    query = db.query(TransitVehicle)
    if route_id:
        query = query.filter(TransitVehicle.route_id.ilike(route_id.strip()))
    
    vehicles = query.order_by(TransitVehicle.updated_at.desc()).limit(limit).all()
    return [TransitVehicleState.model_validate(v) for v in vehicles]


@router.get("/live/trips", response_model=List[NormalizedTripUpdate], summary="List Live Trip Estimates & Delays")
def get_live_trips(
    route_id: Optional[str] = Query(None, description="Filter by Subway Line Route ID"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve live schedule estimates and delay updates."""
    query = db.query(TripUpdateModel)
    if route_id:
        query = query.filter(TripUpdateModel.route_id.ilike(route_id.strip()))
    
    trips = query.order_by(TripUpdateModel.timestamp.desc()).limit(limit).all()
    return [NormalizedTripUpdate.model_validate(t) for t in trips]


@router.get("/live/alerts", response_model=List[NormalizedServiceAlert], summary="List Active Service Alerts")
def get_live_alerts(
    route_id: Optional[str] = Query(None, description="Filter by Subway Line Route ID"),
    db: Session = Depends(get_db)
):
    """Retrieve active MTA Subway service alerts and disruptions."""
    query = db.query(ServiceAlertModel).filter(ServiceAlertModel.active == True)
    
    alerts = query.order_by(ServiceAlertModel.timestamp.desc()).all()
    if route_id:
        alerts = [
            a for a in alerts 
            if a.affected_routes and route_id.upper() in [r.upper() for r in a.affected_routes]
        ]
        
    return [NormalizedServiceAlert.model_validate(a) for a in alerts]


@router.post("/live/sync", summary="Trigger Manual MTA Live Sync")
async def trigger_live_sync(db: Session = Depends(get_db)):
    """Trigger an immediate live MTA Subway feed ingestion cycle."""
    result = await ingestion_service.sync_once(db=db)
    return result
