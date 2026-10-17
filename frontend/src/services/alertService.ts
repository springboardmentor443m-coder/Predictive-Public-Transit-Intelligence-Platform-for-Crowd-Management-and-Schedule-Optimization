import { api } from './api';

export type AlertType = 'OVERCROWDING' | 'LIVE_DELAY' | 'SERVICE_ALERT' | 'NETWORK_IMPACT';
export type AlertSeverity = 'INFO' | 'WARNING' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';

export interface OperationalAlert {
  id: number;
  alert_key: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  description: string;
  entity_id?: string;
  entity_name?: string;
  observed_value?: string;
  predicted_value?: string;
  threshold_info?: string;
  recommended_action?: string;
  acknowledged_by?: string;
  acknowledged_at?: string;
  timestamp: string;
  updated_at: string;
  data_state: string;
}

export interface AlertSummary {
  total_active: number;
  critical_count: number;
  high_count: number;
  warning_count: number;
  info_count: number;
  live_delays_count: number;
  overcrowding_count: number;
  service_alerts_count: number;
  network_impact_count: number;
}

export const alertService = {
  getActiveAlerts: async (severity?: string, alertType?: string): Promise<OperationalAlert[]> => {
    const params: Record<string, any> = {};
    if (severity && severity !== 'ALL') params.severity = severity;
    if (alertType && alertType !== 'ALL') params.alert_type = alertType;
    const response = await api.get<OperationalAlert[]>('/alerts/active', { params });
    return response.data;
  },

  getAlertHistory: async (limit = 100): Promise<OperationalAlert[]> => {
    const response = await api.get<OperationalAlert[]>('/alerts/history', { params: { limit } });
    return response.data;
  },

  getAlertSummary: async (): Promise<AlertSummary> => {
    const response = await api.get<AlertSummary>('/alerts/summary');
    return response.data;
  },

  acknowledgeAlert: async (alertId: number, note?: string): Promise<OperationalAlert> => {
    const response = await api.post<OperationalAlert>(`/alerts/${alertId}/acknowledge`, { note });
    return response.data;
  }
};
