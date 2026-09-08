export interface Station {
  station_code: string;
  name_en: string;
  name_kr?: string;
  line: string;
  latitude: number;
  longitude: number;
  district?: string;
}

export type CongestionLabel = 'low' | 'medium' | 'high' | 'critical';

export interface CrowdPrediction {
  station_code: string;
  timestamp: string;
  predicted_density: number;
  congestion_label: CongestionLabel;
  cached?: boolean;
}

export interface ScheduleRecommendation {
  station_code: string;
  current_density: number;
  congestion_label: CongestionLabel;
  recommended_action: string;
  urgency: string;
  reason: string;
  calculated_at: string;
}

export interface DownstreamAffectedStation {
  station_code: string;
  name_en: string;
  station_order: number;
  estimated_delay_minutes: number;
  estimated_eta_delay_seconds: number;
}

export interface DelayImpact {
  line: string;
  incident_station_code: string;
  incident_station_name: string;
  initial_delay_minutes: number;
  logged_at: string;
  affected_stations: DownstreamAffectedStation[];
}

export interface Alert {
  id: number;
  station_code?: string;
  alert_type: 'overcrowding' | 'delay' | string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  created_at: string;
  resolved: boolean;
}

export interface RidershipHistoryPoint {
  timestamp: string;
  hour: number;
  inflow: number;
  outflow: number;
  total_ridership: number;
  is_weekend: boolean;
}

export interface StationHistory {
  station_code: string;
  station_name: string;
  line: string;
  days: number;
  history: RidershipHistoryPoint[];
}

export interface StationRankingItem {
  station_code: string;
  name_en: string;
  name_kr?: string;
  line: string;
  district?: string;
  total_inflow: number;
  total_outflow: number;
  total_traffic: number;
  alert_count: number;
}

export interface SystemAnalytics {
  total_stations: number;
  total_lines: number;
  total_alerts: number;
  active_alerts: number;
  average_network_occupancy: number;
  busiest_stations: StationRankingItem[];
}

export interface User {
  username: string;
  role: 'admin' | 'operator' | 'viewer';
}
