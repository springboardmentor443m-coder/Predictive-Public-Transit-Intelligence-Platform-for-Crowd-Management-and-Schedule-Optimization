import { api } from './api';

export interface FeedHealthSummary {
  provider_name: string;
  feed_timestamp: string | null;
  received_at: string;
  latency_ms: number;
  entity_count: number;
  status: 'CONNECTING' | 'LIVE' | 'STALE' | 'OFFLINE' | 'ERROR' | 'UNAVAILABLE' | string;
  error_message: string | null;
  is_live: boolean;
}

export interface TransitVehicleState {
  vehicle_id: string;
  trip_id: string | null;
  route_id: string;
  direction_id: number | null;
  current_stop_id: string | null;
  current_stop_sequence: number | null;
  current_status: string | null;
  latitude: number | null;
  longitude: number | null;
  bearing: number | null;
  passenger_count: number | null;
  occupancy_rate: number | null;
  timestamp: string;
  data_state: 'LIVE' | 'UNAVAILABLE' | 'HISTORICAL';
}

export interface NormalizedTripUpdate {
  trip_id: string;
  route_id: string;
  stop_id: string;
  delay_seconds: number;
  estimated_arrival: string | null;
  estimated_departure: string | null;
  timestamp: string;
  data_state: 'LIVE' | 'UNAVAILABLE' | 'HISTORICAL';
}

export interface NormalizedServiceAlert {
  alert_id: string;
  header_text: string;
  description_text: string | null;
  affected_routes: string[];
  affected_stops: string[];
  start_time: string | null;
  end_time: string | null;
  active: boolean;
  timestamp: string;
  data_state: 'LIVE' | 'UNAVAILABLE' | 'HISTORICAL';
}

export const liveService = {
  async getHealth(): Promise<FeedHealthSummary> {
    const response = await api.get<FeedHealthSummary>('/live/health');
    return response.data;
  },

  async getVehicles(routeId?: string): Promise<TransitVehicleState[]> {
    const params = new URLSearchParams();
    if (routeId) params.append('route_id', routeId);
    const response = await api.get<TransitVehicleState[]>('/live/vehicles', { params });
    return response.data;
  },

  async getTrips(routeId?: string): Promise<NormalizedTripUpdate[]> {
    const params = new URLSearchParams();
    if (routeId) params.append('route_id', routeId);
    const response = await api.get<NormalizedTripUpdate[]>('/live/trips', { params });
    return response.data;
  },

  async getAlerts(routeId?: string): Promise<NormalizedServiceAlert[]> {
    const params = new URLSearchParams();
    if (routeId) params.append('route_id', routeId);
    const response = await api.get<NormalizedServiceAlert[]>('/live/alerts', { params });
    return response.data;
  },

  async triggerSync(): Promise<any> {
    const response = await api.post('/live/sync');
    return response.data;
  },
};
