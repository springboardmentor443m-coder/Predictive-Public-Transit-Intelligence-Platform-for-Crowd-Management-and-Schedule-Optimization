// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${res.status} ${path}`);
  return res.json();
}

export const api = {
  // Live
  getLive: () => fetchAPI("/analytics/live"),

  // Station
  getStations: () => fetchAPI("/analytics/stations/list"),
  getStationHourly: (s: string) =>
    fetchAPI(`/analytics/stations/${encodeURIComponent(s)}/hourly`),
  getStationDaily: (s: string) =>
    fetchAPI(`/analytics/stations/${encodeURIComponent(s)}/daily`),
  getStationWeekday: (s: string) =>
    fetchAPI(`/analytics/stations/${encodeURIComponent(s)}/weekday`),
  getStationPredict: (s: string, hours = 6) =>
    fetchAPI(`/analytics/stations/${encodeURIComponent(s)}/predict?hours=${hours}`),

  // Network
  getNetworkDaily: () => fetchAPI("/analytics/network/daily"),
  getNetworkHourly: () => fetchAPI("/analytics/network/hourly"),
  getTopStations: (n = 10, hour?: number) =>
    fetchAPI(`/analytics/network/top-stations?n=${n}${hour !== undefined ? `&hour=${hour}` : ""}`),
  getHeatmap: () => fetchAPI("/analytics/network/heatmap"),
  getLineComparison: () => fetchAPI("/analytics/network/line-comparison"),

  // AI
  getPeakAnalysis: () => fetchAPI("/analytics/ai/peak-analysis"),
  getAnomalies: () => fetchAPI("/analytics/ai/anomalies"),
  getInsights: () => fetchAPI("/analytics/ai/insights"),
  getForecast: () => fetchAPI("/analytics/ai/forecast"),
};
