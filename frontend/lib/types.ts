export interface Station {
  id: string;
  code: string;
  name: string;
  line: string;
  zone: string;
  lat?: number | null;
  lng?: number | null;
  capacity_per_hour: number;
}

export interface LiveCrowdSnapshot {
  station_id: string;
  station_name: string;
  line: string;
  occupancy: number;
  capacity: number;
  occupancy_pct: number;
  congestion_level: string;
  inflow_rate: number;
  outflow_rate: number;
  last_updated: string;
}

export interface StationHeatmapPoint {
  station_id: string;
  station_name: string;
  hour: number;
  occupancy_pct: number;
  congestion_level: string;
}

export interface StationHistoryPoint {
  timestamp: string;
  entries: number;
  exits: number;
  occupancy: number;
  congestion_level: string;
}

export interface TrafficSeriesPoint {
  hour: number;
  passenger_k: number;
  congestion_level: string;
  label?: string;
}

export interface StationPerformance {
  station_id: string;
  station_name: string;
  avg_occupancy_pct: number;
  peak_occupancy_pct: number;
  congestion_score: number;
  entries_total: number;
  exits_total: number;
  punctuality_pct: number | null;
}

export interface AnalyticsOverview {
  total_stations: number;
  total_trains: number;
  active_alerts: number;
  current_overall_occupancy_pct: number;
  avg_occupancy_pct: number;
  on_time_pct: number;
  delayed_count: number;
  predicted_peak_hour: number;
}

export interface PredictionPoint {
  hour: number;
  predicted_occupancy_pct: number;
  lower: number;
  upper: number;
  congestion_level: string;
  timestamp?: string | null;
}

export interface DemandPoint {
  hour: number;
  predicted_entries: number;
  predicted_exits: number;
  peak_probability: number;
}

export interface Recommendation {
  station_id: string;
  station_name: string;
  current_headway_min: number;
  recommended_headway_min: number;
  reason: string;
  capacity_utilization_pct: number;
}

export interface DelayPredictResponse {
  line: string;
  from_station: string;
  to_station: string;
  delay_bucket: string;
  probabilities: Record<string, number>;
  predicted_delay_minutes: number;
}

export interface AlertItem {
  id: string;
  type: string;
  severity: string;
  station_id?: string | null;
  train_id?: string | null;
  title: string;
  message: string;
  is_acknowledged: boolean;
  created_at: string;
  resolved_at?: string | null;
}

export interface ScheduleEntry {
  id: string;
  train_id: string;
  station_id: string;
  direction: string;
  arrival: string;
  departure: string;
  headway_min: number;
  status: string;
  delay_min: number;
  is_peak: string;
  station_name?: string;
}

export interface TrainLive {
  train_id: string;
  line: string;
  model: string;
  capacity: number;
  status: string;
  position_pct: number;
  current_station?: { name?: string } | null;
  next_station?: { name?: string } | null;
  next_eta_min?: number | null;
  delay_min: number;
  load_pct?: number | null;
  last_updated: string;
  direction?: string | null;
  headway_min?: number | null;
}

export interface TrafficPattern {
  station_id: string;
  station_name: string;
  line: string;
  am_peak_hour: number;
  pm_peak_hour: number;
  peak_hour: number;
  peak_occupancy_pct: number;
  weekend_factor: number;
}

export interface InsightAction {
  station_id?: string;
  station_name?: string;
  action?: string;
  reason?: string;
  utilization_pct?: number;
}

export interface InsightStation {
  station_id: string;
  station_name: string;
  occupancy_pct: number;
  congestion_level: string;
}

export interface InsightDemandOutlook {
  station_id?: string;
  station_name?: string;
  next_3h_entries?: number[];
}

export interface AiInsights {
  generated_at: string;
  network_status: string;
  predicted_peak_hour?: number | null;
  on_time_pct?: number | null;
  critical_stations?: InsightStation[];
  top_actions?: InsightAction[];
  demand_outlook?: InsightDemandOutlook[];
  patterns_summary?: Array<Record<string, unknown>>;
  open_alerts: number;
  recommendations_count: number;
}

export interface ModelMetricInfo {
  r2?: number;
  mae?: number;
  auc?: number;
}

export interface ModelSubInfo {
  algorithm?: string;
  metrics?: ModelMetricInfo;
}

export interface ModelInfo {
  city: string;
  crowd?: ModelSubInfo;
  demand?: ModelSubInfo;
  delay?: ModelSubInfo;
  datasets?: Record<string, string>;
  station_map?: Record<string, unknown>;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}