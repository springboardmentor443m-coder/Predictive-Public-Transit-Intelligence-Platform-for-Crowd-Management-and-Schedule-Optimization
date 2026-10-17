from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class MLSummaryResponse(BaseModel):
    total_stations: int
    total_prediction_records: int
    low_count: int
    moderate_count: int
    high_count: int
    critical_count: int
    latest_prediction_time: str
    high_risk_stations_count: int
    critical_risk_stations_count: int
    next_hour_total_predicted_demand: float
    mae: float
    rmse: float
    r2: float
    data_state: str

    model_config = ConfigDict(from_attributes=True)

class MLPredictionRecord(BaseModel):
    transit_timestamp: str
    station_complex_id: str
    station_complex: str
    passenger_count: float
    target_next_hour: float
    predicted_next_hour: float
    absolute_error: float
    crowd_risk: str
    recommended_action: str

    model_config = ConfigDict(from_attributes=True)

class MLStationStatusResponse(BaseModel):
    station_complex_id: str
    station_complex: str
    latest_passenger_count: float
    predicted_next_hour: float
    absolute_error: float
    crowd_risk: str
    risk_explanation: str
    recommended_action: str
    transit_timestamp: str
    data_state: str

    model_config = ConfigDict(from_attributes=True)

class RiskDistributionItem(BaseModel):
    risk: str
    count: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)

class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float

    model_config = ConfigDict(from_attributes=True)

class StationHistoryRecord(BaseModel):
    timestamp: str
    passenger_count: float
    predicted_next_hour: float
    crowd_risk: str

    model_config = ConfigDict(from_attributes=True)

class MLStationDetailResponse(BaseModel):
    station_complex_id: str
    station_complex: str
    latest_passenger_count: float
    predicted_next_hour: float
    crowd_risk: str
    recommended_action: str
    latest_timestamp: str
    history: List[StationHistoryRecord]

    model_config = ConfigDict(from_attributes=True)

class NetworkSummaryResponse(BaseModel):
    total_nodes: int
    total_edges: int
    delay_model_accuracy: Optional[float] = None
    network_model_accuracy: Optional[float] = None
    high_network_risk_nodes: Optional[int] = None
    critical_network_risk_nodes: Optional[int] = None
    moderate_network_risk_nodes: Optional[int] = None
    data_state: str

    model_config = ConfigDict(from_attributes=True)

class DelayImpactRecord(BaseModel):
    route_id: str
    delay_seconds: float
    severity_tier: str
    affected_stations_count: int
    data_state: str

    model_config = ConfigDict(from_attributes=True)

class NetworkRiskRecord(BaseModel):
    station_complex_id: str
    station_complex: str
    predicted_next_hour: float
    neighbor_predicted_demand: float
    network_pressure_ratio: float
    network_risk: str
    contributing_factors: List[str]
    recommended_action: str

    model_config = ConfigDict(from_attributes=True)

class StationConnectionsResponse(BaseModel):
    station_complex_id: str
    station_complex: str
    routes: List[str]
    degree: int
    transfer_hub: bool
    neighbors: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)

class SchedulingIntelligenceRecord(BaseModel):
    station_complex_id: str
    station_complex: str
    routes: List[str]
    predicted_demand_next_hour: float
    demand_pressure_ratio: float
    crowd_risk: str
    current_headway_minutes: float
    recommended_headway_minutes: float
    headway_delta_percent: float
    recommended_action: str
    advisory_tier: str
    advisory_disclaimer: str
    data_state: str

    model_config = ConfigDict(from_attributes=True)

class HourlyPatternItem(BaseModel):
    hour: int
    avg_passenger_count: float
    predicted_avg_count: float
    is_current_hour: Optional[bool] = None
    live_current_demand: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class WeekdayPatternItem(BaseModel):
    day: str
    avg_passenger_count: float

    model_config = ConfigDict(from_attributes=True)

class TopStationItem(BaseModel):
    station_complex_id: str
    station_complex: str
    total_observed_volume: float
    avg_hourly_demand: float
    peak_demand: float

    model_config = ConfigDict(from_attributes=True)

class PeakSummary(BaseModel):
    peak_hour_avg: float
    off_peak_hour_avg: float
    peak_multiplier: float
    current_hour: Optional[int] = None
    current_live_system_demand: Optional[float] = None
    is_peak_now: Optional[bool] = None
    live_system_load_ratio: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class TrafficAnalyticsResponse(BaseModel):
    hourly_patterns: List[HourlyPatternItem]
    weekday_patterns: List[WeekdayPatternItem]
    top_stations: List[TopStationItem]
    peak_summary: PeakSummary
    data_state: str = "HISTORICAL MTA RIDERSHIP"

    model_config = ConfigDict(from_attributes=True)


class AnomalyRecord(BaseModel):
    station_complex_id: str
    station_complex: str
    observed_value: float
    baseline_value: float
    time_window: str
    reason: str
    timestamp: str

    model_config = ConfigDict(from_attributes=True)

class AnomalyDetectionResponse(BaseModel):
    is_available: bool
    status_message: str
    anomalies: List[AnomalyRecord]

    model_config = ConfigDict(from_attributes=True)


# ── Real-time ML Crowd Prediction schemas ──────────────────────────────────────

class RealtimeStationPrediction(BaseModel):
    station_complex_id: str
    station_complex: str
    routes: List[str]
    current_passenger_count: float
    predicted_next_hour: float
    crowd_risk: str                   # LOW | MODERATE | HIGH | CRITICAL
    confidence: float                 # 0–1 model confidence
    avg_live_delay_seconds: float
    delay_escalation_note: str
    recommended_action: str
    is_live_model: bool
    prediction_time: str
    data_state: str

    model_config = ConfigDict(from_attributes=True)


class RealtimeCrowdPredictionResponse(BaseModel):
    prediction_time: str
    is_live_model: bool
    stations_predicted: int
    live_model_stations: int
    total_predicted_demand_next_hour: float
    risk_summary: Dict[str, int]
    high_risk_count: int
    system_hour: int
    is_peak_hour: bool
    active_delay_routes: int
    predictions: List[RealtimeStationPrediction]
    data_state: str

    model_config = ConfigDict(from_attributes=True)

