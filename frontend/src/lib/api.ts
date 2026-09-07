import {
  StationDensity, CrowdSummary, TrainSchedule, FrequencyRecommendation,
  StationForecast, AlertItem, AnalyticsSummary, User, DatasetStats
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("metroflow_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: { ...headers, ...options?.headers },
  });

  if (!res.ok) {
    const errorMsg = await res.text();
    throw new Error(errorMsg || `API Request failed with status ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Auth
  login: async (email: string, password: string) => {
    return fetchJson<{ access_token: string; refresh_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
  getMe: async () => fetchJson<User>("/auth/me"),

  // Crowd
  getDensities: async () => fetchJson<StationDensity[]>("/crowd/densities"),
  getCrowdSummary: async () => fetchJson<CrowdSummary>("/crowd/summary"),

  // Schedules
  getSchedules: async () => fetchJson<TrainSchedule[]>("/schedules/"),
  getOptimizations: async () => fetchJson<FrequencyRecommendation[]>("/schedules/optimizations"),
  overrideSchedule: async (schedule_id: number, new_headway_minutes: number, reason: string) => {
    return fetchJson<{ applied: boolean; message: string }>("/schedules/override", {
      method: "POST",
      body: JSON.stringify({ schedule_id, new_headway_minutes, reason }),
    });
  },

  // Predictions
  getStationForecast: async (stationId: number, horizon = 30) => {
    return fetchJson<StationForecast>(`/predictions/forecast/${stationId}?horizon=${horizon}`);
  },
  getAllForecasts: async (horizon = 30) => {
    return fetchJson<StationForecast[]>(`/predictions/all?horizon=${horizon}`);
  },
  getAnomalies: async () => fetchJson<any[]>("/predictions/anomalies"),

  // Alerts
  getAlerts: async () => fetchJson<AlertItem[]>("/alerts/"),
  triggerPABroadcast: async (stationIds: number[], message: string, priority = "WARNING") => {
    return fetchJson<{ broadcast_id: string; status: string }>("/alerts/broadcast", {
      method: "POST",
      body: JSON.stringify({ station_ids: stationIds, message, priority }),
    });
  },
  resolveAlert: async (alertId: string) => {
    return fetchJson<{ alert_id: string; resolved: boolean }>(`/alerts/resolve/${alertId}`, {
      method: "POST",
    });
  },

  // Analytics
  getAnalyticsSummary: async () => fetchJson<AnalyticsSummary>("/analytics/summary"),
  getExportCsvUrl: () => `${API_BASE}/analytics/export/csv`,

  // Real-World Datasets & Retraining
  getDatasetStats: async () => fetchJson<DatasetStats>("/datasets/stats"),
  ingestDatasets: async () => fetchJson<{ status: string; message: string }>("/datasets/ingest", { method: "POST" }),
  retrainModels: async () => fetchJson<{ status: string; message: string; metrics: any; dataset_rows?: number }>("/datasets/retrain", { method: "POST" }),
};
