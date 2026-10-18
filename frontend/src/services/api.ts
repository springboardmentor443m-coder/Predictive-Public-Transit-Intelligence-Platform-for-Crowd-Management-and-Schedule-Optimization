import { User, NetworkSnapshot, Station, Alert, LineSchedule, HorizonPrediction } from '../types';

const API_BASE = 'http://localhost:8000/api';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('metroflow_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const api = {
  // Auth
  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    localStorage.setItem('metroflow_token', data.access_token);
    localStorage.setItem('metroflow_user', JSON.stringify(data.user));
    return data;
  },

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('metroflow_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  logout() {
    localStorage.removeItem('metroflow_token');
    localStorage.removeItem('metroflow_user');
  },

  async listUsers(): Promise<User[]> {
    const res = await fetch(`${API_BASE}/auth/users`, {
      headers: { ...getAuthHeader() }
    });
    const data = await res.json();
    return data.users;
  },

  async createUser(userData: any): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(userData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create user');
    }
    return res.json();
  },

  // Crowd Monitoring
  async getLiveSnapshot(): Promise<NetworkSnapshot> {
    const res = await fetch(`${API_BASE}/crowd/live`);
    return res.json();
  },

  async getStationDetails(stationId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/crowd/station/${stationId}`);
    return res.json();
  },

  async getFlowAnalysis(): Promise<any> {
    const res = await fetch(`${API_BASE}/crowd/flow-analysis`);
    return res.json();
  },

  // Predictions
  async getStationMultiHorizon(stationId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/predictions/station/${stationId}`);
    return res.json();
  },

  async getNetworkHorizonPredictions(minutes: number): Promise<{ horizon_minutes: number; horizon_label: string; average_network_density: number; critical_stations_count: number; stations: HorizonPrediction[] }> {
    const res = await fetch(`${API_BASE}/predictions/horizon/${minutes}`);
    return res.json();
  },

  async getSmartRecommendations(): Promise<any> {
    const res = await fetch(`${API_BASE}/predictions/recommendations`);
    return res.json();
  },

  // Scheduling
  async getLineSchedules(): Promise<LineSchedule[]> {
    const res = await fetch(`${API_BASE}/scheduling/lines`);
    const data = await res.json();
    return data.lines;
  },

  async adjustLineFrequency(line: string, target_headway: number, reason?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/scheduling/frequency-adjust`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ line, target_headway, reason })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Frequency adjustment failed');
    }
    return res.json();
  },

  async optimizePeakSchedules(): Promise<any> {
    const res = await fetch(`${API_BASE}/scheduling/optimize-peak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() }
    });
    return res.json();
  },

  async reportTrainDelay(train_id: string, delay_minutes: number, cause: string): Promise<any> {
    const res = await fetch(`${API_BASE}/scheduling/report-delay`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ train_id, delay_minutes, cause })
    });
    return res.json();
  },

  // Alerts
  async getAlerts(): Promise<{ alerts: Alert[]; active_count: number }> {
    const res = await fetch(`${API_BASE}/alerts`);
    return res.json();
  },

  async broadcastAlert(data: { severity: string; category: string; message: string; station_id?: string; station_name?: string; line?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/alerts/broadcast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async resolveAlert(alertId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() }
    });
    return res.json();
  },

  // Analytics
  async getAnalyticsOverview(): Promise<any> {
    const res = await fetch(`${API_BASE}/analytics/overview`);
    return res.json();
  },

  async getHourlyPatterns(): Promise<any> {
    const res = await fetch(`${API_BASE}/analytics/hourly-patterns`);
    return res.json();
  },

  async getStationRankings(): Promise<any> {
    const res = await fetch(`${API_BASE}/analytics/station-rankings`);
    return res.json();
  },

  async getAuditLogs(): Promise<any> {
    const res = await fetch(`${API_BASE}/analytics/audit-logs`);
    return res.json();
  }
};
