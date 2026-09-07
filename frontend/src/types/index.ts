export type UserRole = "ADMIN" | "OPERATOR" | "VIEWER";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  assigned_station_id?: number | null;
  is_active: boolean;
}

export interface StationDensity {
  station_id: number;
  station_code: string;
  station_name: string;
  line_name: string;
  inflow_rate_ppm: number;
  outflow_rate_ppm: number;
  current_occupancy: number;
  platform_capacity: number;
  density_percentage: number;
  status: "NORMAL" | "MODERATE" | "CRITICAL";
  latitude: number;
  longitude: number;
  is_interchange: boolean;
  last_updated: string;
}

export interface CrowdSummary {
  total_system_occupancy: number;
  average_density_percentage: number;
  critical_stations_count: number;
  moderate_stations_count: number;
  normal_stations_count: number;
  stations: StationDensity[];
}

export interface TrainSchedule {
  id: number;
  train_id: number;
  train_code: string;
  line_name: string;
  origin_station_id: number;
  origin_station_name: string;
  destination_station_id: number;
  destination_station_name: string;
  departure_time: string;
  arrival_time: string;
  headway_minutes: number;
  recommended_headway: number;
  status: "SCHEDULED" | "RUNNING" | "DELAYED" | "COMPLETED" | "CANCELLED";
  delay_minutes: number;
  conflict_detected: boolean;
  conflict_reason?: string;
}

export interface FrequencyRecommendation {
  line_name: string;
  segment_name: string;
  current_headway_minutes: number;
  recommended_headway_minutes: number;
  additional_trains_needed: number;
  reason: string;
  crowd_density_percentage: number;
  timestamp: string;
}

export interface DemandForecastPoint {
  timestamp: string;
  predicted_inflow: number;
  predicted_outflow: number;
  confidence_interval_lower: number;
  confidence_interval_upper: number;
  surge_probability: number;
}

export interface StationForecast {
  station_id: number;
  station_name: string;
  line_name: string;
  forecast_horizon_minutes: number;
  current_density_pct: number;
  predicted_peak_density_pct: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "SEVERE" | "CRITICAL";
  surge_probability: number;
  forecast_points: DemandForecastPoint[];
}

export interface AlertItem {
  id: string;
  station_id?: number;
  station_name?: string;
  line_name?: string;
  priority: "INFO" | "WARNING" | "CRITICAL";
  category: "OVERCROWDING" | "TRAIN_DELAY" | "EMERGENCY_HALT" | "ANOMALY";
  message: string;
  timestamp: string;
  is_resolved: boolean;
}

export interface AnalyticsSummary {
  total_daily_passengers: number;
  overall_otp_percentage: number;
  active_trains_count: number;
  critical_incidents_today: number;
  peak_rush_hour: string;
  line_performances: {
    line_name: string;
    active_trains: number;
    on_time_performance_pct: number;
    avg_delay_minutes: number;
    total_daily_ridership: number;
    peak_crowd_station: string;
  }[];
  ridership_trends: {
    time_label: string;
    total_inflow: number;
    total_outflow: number;
    avg_density_pct: number;
  }[];
}

export interface DatasetStats {
  total_records: number;
  data_sources: string[];
  date_range: string;
  master_file_exists: boolean;
  last_trained_r2?: number;
  last_trained_mae?: number;
}
