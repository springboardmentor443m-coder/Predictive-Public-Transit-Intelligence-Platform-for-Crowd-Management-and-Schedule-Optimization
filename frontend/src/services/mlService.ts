import { api } from './api';

export interface MLSummary {
  total_stations: number;
  total_prediction_records: number;
  low_count: number;
  moderate_count: number;
  high_count: number;
  critical_count: number;
  latest_prediction_time: string;
  high_risk_stations_count: number;
  critical_risk_stations_count: number;
  next_hour_total_predicted_demand: number;
  mae: number;
  rmse: number;
  r2: number;
  data_state: string;
}

export interface MLStationStatus {
  station_complex_id: string;
  station_complex: string;
  latest_passenger_count: number;
  predicted_next_hour: number;
  absolute_error: number;
  crowd_risk: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | string;
  risk_explanation?: string;
  recommended_action: string;
  transit_timestamp: string;
  data_state: string;
}

export interface RiskDistribution {
  risk: string;
  count: number;
  percentage: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface MLPredictionRecord {
  transit_timestamp: string;
  station_complex_id: string;
  station_complex: string;
  passenger_count: number;
  target_next_hour: number;
  predicted_next_hour: number;
  absolute_error: number;
  crowd_risk: string;
  recommended_action: string;
}

export interface StationHistoryRecord {
  timestamp: string;
  passenger_count: number;
  predicted_next_hour: number;
  crowd_risk: string;
}

export interface MLStationDetail {
  station_complex_id: string;
  station_complex: string;
  latest_passenger_count: number;
  predicted_next_hour: number;
  crowd_risk: string;
  recommended_action: string;
  latest_timestamp: string;
  history: StationHistoryRecord[];
}

export interface NetworkSummary {
  total_nodes: number;
  total_edges: number;
  delay_model_accuracy: number | null;
  network_model_accuracy: number | null;
  high_network_risk_nodes: number | null;
  critical_network_risk_nodes: number | null;
  data_state: string;
}

export interface DelayImpactRecord {
  route_id: string;
  delay_seconds: number;
  severity_tier: string;
  affected_stations_count: number;
  data_state: string;
}

export interface NetworkRiskRecord {
  station_complex_id: string;
  station_complex: string;
  predicted_next_hour: number;
  neighbor_predicted_demand: number;
  network_pressure_ratio: number;
  network_risk: string;
  contributing_factors: string[];
  recommended_action: string;
}

export interface NeighborInfo {
  station_complex_id: string;
  name: string;
  routes: string[];
  transfer_hub: boolean;
}

export interface StationConnections {
  station_complex_id: string;
  station_complex: string;
  routes: string[];
  degree: number;
  transfer_hub: boolean;
  neighbors: NeighborInfo[];
}

export interface SchedulingIntelligenceRecord {
  station_complex_id: string;
  station_complex: string;
  routes: string[];
  predicted_demand_next_hour: number;
  demand_pressure_ratio: number;
  crowd_risk: string;
  current_headway_minutes: number;
  recommended_headway_minutes: number;
  headway_delta_percent: number;
  recommended_action: string;
  advisory_tier: string;
  advisory_disclaimer: string;
  data_state: string;
}

export interface HourlyPatternItem {
  hour: number;
  avg_passenger_count: number;
  predicted_avg_count: number;
  is_current_hour?: boolean;
  live_current_demand?: number;
}

export interface WeekdayPatternItem {
  day: string;
  avg_passenger_count: number;
}

export interface TopStationItem {
  station_complex_id: string;
  station_complex: string;
  total_observed_volume: number;
  avg_hourly_demand: number;
  peak_demand: number;
}

export interface PeakSummary {
  peak_hour_avg: number;
  off_peak_hour_avg: number;
  peak_multiplier: number;
  current_hour?: number;
  current_live_system_demand?: number;
  is_peak_now?: boolean;
  live_system_load_ratio?: number;
}

export interface TrafficAnalyticsResponse {
  hourly_patterns: HourlyPatternItem[];
  weekday_patterns: WeekdayPatternItem[];
  top_stations: TopStationItem[];
  peak_summary: PeakSummary;
  data_state: string;
}

export interface AnomalyRecord {
  station_complex_id: string;
  station_complex: string;
  observed_value: number;
  baseline_value: number;
  time_window: string;
  reason: string;
  timestamp: string;
}

export interface AnomalyDetectionResponse {
  is_available: boolean;
  status_message: string;
  anomalies: AnomalyRecord[];
}

// ── Real-time ML Crowd Prediction ─────────────────────────────────────────────

export interface RealtimeStationPrediction {
  station_complex_id: string;
  station_complex: string;
  routes: string[];
  current_passenger_count: number;
  predicted_next_hour: number;
  crowd_risk: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | string;
  confidence: number;
  avg_live_delay_seconds: number;
  delay_escalation_note: string;
  recommended_action: string;
  is_live_model: boolean;
  prediction_time: string;
  data_state: string;
}

export interface RealtimeCrowdPredictionResponse {
  prediction_time: string;
  is_live_model: boolean;
  stations_predicted: number;
  live_model_stations: number;
  total_predicted_demand_next_hour: number;
  risk_summary: Record<string, number>;
  high_risk_count: number;
  system_hour: number;
  is_peak_hour: boolean;
  active_delay_routes: number;
  predictions: RealtimeStationPrediction[];
  data_state: string;
}

// ─────────────────────────────────────────────────────────────────────────────

export const mlService = {
  getSummary: async (): Promise<MLSummary> => {
    const response = await api.get<MLSummary>('/ml/summary');
    return response.data;
  },

  getStations: async (): Promise<MLStationStatus[]> => {
    const response = await api.get<MLStationStatus[]>('/ml/stations');
    return response.data;
  },

  getRiskDistribution: async (): Promise<RiskDistribution[]> => {
    const response = await api.get<RiskDistribution[]>('/ml/risk-distribution');
    return response.data;
  },

  getFeatureImportance: async (): Promise<FeatureImportance[]> => {
    const response = await api.get<FeatureImportance[]>('/ml/feature-importance');
    return response.data;
  },

  getPredictions: async (station?: string, risk?: string, limit = 100): Promise<MLPredictionRecord[]> => {
    const params: Record<string, any> = { limit };
    if (station) params.station = station;
    if (risk) params.risk = risk;
    const response = await api.get<MLPredictionRecord[]>('/ml/predictions', { params });
    return response.data;
  },

  getStationDetail: async (stationName: string): Promise<MLStationDetail> => {
    const response = await api.get<MLStationDetail>(`/ml/station/${encodeURIComponent(stationName)}`);
    return response.data;
  },

  getNetworkSummary: async (): Promise<NetworkSummary> => {
    const response = await api.get<NetworkSummary>('/ml/network-summary');
    return response.data;
  },

  getDelayImpact: async (): Promise<DelayImpactRecord[]> => {
    const response = await api.get<DelayImpactRecord[]>('/ml/delay-impact');
    return response.data;
  },

  getNetworkRisk: async (): Promise<NetworkRiskRecord[]> => {
    const response = await api.get<NetworkRiskRecord[]>('/ml/network-risk');
    return response.data;
  },

  getStationConnections: async (stationName: string): Promise<StationConnections> => {
    const response = await api.get<StationConnections>(`/ml/station/${encodeURIComponent(stationName)}/connections`);
    return response.data;
  },

  getSchedulingIntelligence: async (): Promise<SchedulingIntelligenceRecord[]> => {
    const response = await api.get<SchedulingIntelligenceRecord[]>('/ml/scheduling-intelligence');
    return response.data;
  },

  getTrafficAnalytics: async (): Promise<TrafficAnalyticsResponse> => {
    const response = await api.get<TrafficAnalyticsResponse>('/ml/analytics/traffic');
    return response.data;
  },

  getAnomalies: async (): Promise<AnomalyDetectionResponse> => {
    const response = await api.get<AnomalyDetectionResponse>('/ml/anomalies');
    return response.data;
  },

  /** Real-time RandomForest predictions enriched with live GTFS-RT delay data */
  getRealtimeCrowdPrediction: async (): Promise<RealtimeCrowdPredictionResponse> => {
    const response = await api.get<RealtimeCrowdPredictionResponse>('/ml/crowd-prediction');
    return response.data;
  },
};
