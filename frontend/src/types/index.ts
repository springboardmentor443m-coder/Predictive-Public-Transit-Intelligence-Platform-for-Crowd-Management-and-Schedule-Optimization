export interface User {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'operator';
  title: string;
  badge_id: string;
}

export interface Station {
  id: string;
  name: string;
  borough: string;
  lat: number;
  lon: number;
  lines: string[];
  zone: string;
  capacity: number;
  current_occupancy: number;
  density_percent: number;
  congestion_level: 'Low' | 'Moderate' | 'High' | 'Severe';
  inflow_rate: number;
  outflow_rate: number;
  turnstiles: number;
  turnstiles_active: number;
  trend: 'rising' | 'falling' | 'steady';
  last_train_arrival?: string;
}

export interface Train {
  id: string;
  line: string;
  line_name: string;
  line_color: string;
  from_station_id: string;
  from_station_name: string;
  to_station_id: string;
  to_station_name: string;
  progress: number;
  lat: number;
  lon: number;
  speed_mph: number;
  occupancy_percent: number;
  cars: number;
  delay_seconds: number;
  status: string;
}

export interface Alert {
  id: number;
  severity: 'info' | 'warning' | 'critical' | 'emergency';
  category: 'overcrowding' | 'delay' | 'emergency' | 'maintenance';
  station_id?: string;
  station_name?: string;
  line?: string;
  message: string;
  timestamp: string;
  is_active: number | boolean;
  resolved_by?: string;
}

export interface LineSchedule {
  line: string;
  name: string;
  color: string;
  current_headway: number;
  recommended_headway: number;
  peak_status: string;
  active_train_count: number;
  status: string;
  last_updated: string;
}

export interface HorizonPrediction {
  station_id: string;
  station_name: string;
  borough: string;
  horizon_minutes: number;
  horizon_label: string;
  predicted_timestamp: string;
  predicted_density_percent: number;
  estimated_passenger_count: number;
  platform_capacity: number;
  projected_inflow_rate: number;
  projected_outflow_rate: number;
  congestion_level: 'Low' | 'Moderate' | 'High' | 'Severe';
  risk_color: string;
  recommended_headway_mins: number;
  recommendations: string[];
  lat?: number;
  lon?: number;
  lines?: string[];
}

export interface NetworkSnapshot {
  timestamp: string;
  network_metrics: {
    active_network_passengers: number;
    network_capacity: number;
    overall_density_percent: number;
    total_inflow_rate: number;
    total_outflow_rate: number;
    active_trains_count: number;
    stations_monitored: number;
    severe_congestion_stations: number;
    high_congestion_stations: number;
    moderate_congestion_stations: number;
    normal_stations: number;
    system_status: string;
  };
  stations: Station[];
  trains: Train[];
}
