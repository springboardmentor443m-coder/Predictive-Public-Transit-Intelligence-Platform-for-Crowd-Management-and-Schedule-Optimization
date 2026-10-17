from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_operator_or_admin
from app.models.user import User
from app.services.ml_service import MLDataService
from app.schemas.ml import (
    MLSummaryResponse,
    MLPredictionRecord,
    MLStationStatusResponse,
    RiskDistributionItem,
    FeatureImportanceItem,
    MLStationDetailResponse,
    NetworkSummaryResponse,
    DelayImpactRecord,
    NetworkRiskRecord,
    StationConnectionsResponse,
    SchedulingIntelligenceRecord,
    TrafficAnalyticsResponse,
    AnomalyDetectionResponse,
    RealtimeCrowdPredictionResponse,
)

# All ML endpoints require a valid JWT + operator or admin role
router = APIRouter(
    prefix="/ml",
    tags=["ML Demand & Risk Intelligence"],
    dependencies=[Depends(require_operator_or_admin)],
)

def get_ml_service():
    return MLDataService.get_instance()

@router.get("/summary", response_model=MLSummaryResponse)
def get_ml_summary(service: MLDataService = Depends(get_ml_service), db: Session = Depends(get_db)):
    """Returns overall ML model performance metrics and crowd risk counts."""
    return service.get_summary(db=db)

@router.get("/predictions", response_model=List[MLPredictionRecord])
def get_ml_predictions(
    station: Optional[str] = Query(None, description="Station complex name or ID filter"),
    risk: Optional[str] = Query(None, description="Risk level filter (LOW, MODERATE, HIGH, CRITICAL)"),
    limit: int = Query(100, ge=1, le=5000, description="Max records to return"),
    service: MLDataService = Depends(get_ml_service)
):
    """Returns prediction records with optional station or risk filtering."""
    return service.get_predictions(station=station, risk=risk, limit=limit)

@router.get("/stations", response_model=List[MLStationStatusResponse])
def get_ml_stations(service: MLDataService = Depends(get_ml_service), db: Session = Depends(get_db)):
    """Returns current/latest forecast status for all 12 target stations."""
    return service.get_stations_latest(db)

@router.get("/risk-distribution", response_model=List[RiskDistributionItem])
def get_risk_distribution(service: MLDataService = Depends(get_ml_service)):
    """Returns crowd risk distribution counts and percentages."""
    return service.get_risk_distribution()

@router.get("/feature-importance", response_model=List[FeatureImportanceItem])
def get_feature_importance(service: MLDataService = Depends(get_ml_service)):
    """Returns feature importance rankings from the Random Forest model."""
    return service.get_feature_importance()

@router.get("/network-summary", response_model=NetworkSummaryResponse)
def get_network_summary(service: MLDataService = Depends(get_ml_service), db: Session = Depends(get_db)):
    """Returns topological station network metrics and model accuracy."""
    return service.get_network_summary(db=db)

@router.get("/delay-impact", response_model=List[DelayImpactRecord])
def get_delay_impact(service: MLDataService = Depends(get_ml_service), db: Session = Depends(get_db)):
    """Returns route-level delay impact severity estimates."""
    return service.get_delay_impact(db)

@router.get("/network-risk", response_model=List[NetworkRiskRecord])
def get_network_risk(service: MLDataService = Depends(get_ml_service), db: Session = Depends(get_db)):
    """Returns connected-station congestion pressure and explainable factors."""
    return service.get_network_risk(db=db)

@router.get("/station/{station_name}", response_model=MLStationDetailResponse)
def get_station_detail(
    station_name: str,
    service: MLDataService = Depends(get_ml_service)
):
    """Returns detailed history and forecasts for a specific station."""
    return service.get_station_detail(station_name)

@router.get("/station/{station_name}/connections", response_model=StationConnectionsResponse)
def get_station_connections(
    station_name: str,
    service: MLDataService = Depends(get_ml_service)
):
    """Returns topological graph connections and neighbors for a station."""
    return service.get_station_connections(station_name)

@router.get("/scheduling-intelligence", response_model=List[SchedulingIntelligenceRecord])
def get_scheduling_intelligence(service: MLDataService = Depends(get_ml_service), db: Session = Depends(get_db)):
    """Returns AI-driven peak-hour scheduling recommendations and headway optimization advisories."""
    return service.get_scheduling_intelligence(db)

@router.get("/analytics/traffic", response_model=TrafficAnalyticsResponse)
def get_traffic_analytics(service: MLDataService = Depends(get_ml_service), db: Session = Depends(get_db)):
    """Returns passenger traffic demand patterns, peak hours, and live system load indices."""
    return service.get_traffic_analytics(db=db)

@router.get("/anomalies", response_model=AnomalyDetectionResponse)
def get_anomalies(service: MLDataService = Depends(get_ml_service)):
    """Detects unusual ridership/delays relative to baselines."""
    return service.get_anomalies()


@router.get("/crowd-prediction", response_model=RealtimeCrowdPredictionResponse)
def get_realtime_crowd_prediction(
    service: MLDataService = Depends(get_ml_service),
    db: Session = Depends(get_db)
):
    """
    Real-time crowd demand prediction using the trained RandomForest model.
    Features are built from current clock time + live GTFS-RT delay data from DB.
    Returns station-level predictions with risk tier, confidence scores,
    and actionable operator recommendations.
    """
    return service.get_realtime_crowd_predictions(db=db)
