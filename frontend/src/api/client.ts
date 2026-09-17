import {
  Station,
  CrowdPrediction,
  ScheduleRecommendation,
  DelayImpact,
  Alert,
  StationHistory,
  SystemAnalytics,
} from '../types';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('metroflow_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('metroflow_token', token);
    } else {
      localStorage.removeItem('metroflow_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch (e) {
        // Fallback to status text
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  // Stations
  async getStations(params?: { search?: string; line?: string; district?: string }): Promise<Station[]> {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.line) query.append('line', params.line);
    if (params?.district) query.append('district', params.district);
    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request<Station[]>(`/api/v1/stations${queryString}`);
  }

  async getStation(stationCode: string): Promise<Station> {
    return this.request<Station>(`/api/v1/stations/${encodeURIComponent(stationCode)}`);
  }

  async getStationHistory(stationCode: string, days = 7): Promise<StationHistory> {
    return this.request<StationHistory>(`/api/v1/stations/${encodeURIComponent(stationCode)}/history?days=${days}`);
  }

  // Prediction
  async predictCrowd(stationCode: string, timestamp?: string): Promise<CrowdPrediction> {
    const ts = timestamp || new Date().toISOString();
    return this.request<CrowdPrediction>('/api/v1/predict/crowd', {
      method: 'POST',
      body: JSON.stringify({
        station_code: stationCode,
        timestamp: ts,
      }),
    });
  }

  // Scheduling
  async getScheduleRecommendation(stationCode: string): Promise<ScheduleRecommendation> {
    return this.request<ScheduleRecommendation>(`/api/v1/schedule/recommend/${encodeURIComponent(stationCode)}`);
  }

  async reportDelay(line: string, stationCode: string, delayMinutes: number): Promise<DelayImpact> {
    return this.request<DelayImpact>('/api/v1/schedule/delay', {
      method: 'POST',
      body: JSON.stringify({
        line,
        station_code: stationCode,
        delay_minutes: delayMinutes,
      }),
    });
  }

  // Alerts
  async getAlerts(params?: { severity?: string; station_code?: string; resolved?: boolean }): Promise<Alert[]> {
    const query = new URLSearchParams();
    if (params?.severity) query.append('severity', params.severity);
    if (params?.station_code) query.append('station_code', params.station_code);
    if (params?.resolved !== undefined) query.append('resolved', String(params.resolved));
    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request<Alert[]>(`/api/v1/alerts${queryString}`);
  }

  async resolveAlert(alertId: number): Promise<Alert> {
    return this.request<Alert>(`/api/v1/alerts/resolve/${alertId}`, {
      method: 'POST',
    });
  }

  // Analytics
  async getAnalyticsOverview(limit = 10): Promise<SystemAnalytics> {
    return this.request<SystemAnalytics>(`/api/v1/analytics/overview?limit=${limit}`);
  }

  // Auth
  async login(username: string, password: string): Promise<{ access_token: string; token_type: string; role: string; username: string }> {
    const result = await this.request<{ access_token: string; token_type: string; role: string; username: string }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.setToken(result.access_token);
    return result;
  }

  logout() {
    this.setToken(null);
  }
}

export const api = new ApiClient();
