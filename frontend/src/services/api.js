import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Automatically attach JWT token to protected API requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("metroflow_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// ---------------------------------------------------------
// AUTHENTICATION
// ---------------------------------------------------------

export const loginUser = async (username, password) => {
  const response = await api.post("/auth/login", {
    username,
    password,
  });

  const token = response.data.access_token;
  localStorage.setItem("metroflow_token", token);

  return response.data;
};

export const logoutUser = () => {
  localStorage.removeItem("metroflow_token");
};

export const isAuthenticated = () => {
  return Boolean(localStorage.getItem("metroflow_token"));
};

// ---------------------------------------------------------
// NETWORK MONITORING
// ---------------------------------------------------------

export const getNetworkMonitoring = async (date, hour) => {
  const response = await api.get("/monitoring/summary", {
    params: { date, hour },
  });

  return response.data;
};

// ---------------------------------------------------------
// NETWORK ALERTS
// ---------------------------------------------------------

export const getNetworkAlerts = async (date, hour) => {
  const response = await api.get("/alerts/summary", {
    params: { date, hour },
  });

  return response.data;
};

// ---------------------------------------------------------
// SCHEDULING INTELLIGENCE
// ---------------------------------------------------------

export const getNetworkScheduling = async () => {
  const response = await api.get("/scheduling/intelligence/summary");
  return response.data;
};

// ---------------------------------------------------------
// OPERATIONS DECISION SUPPORT
// ---------------------------------------------------------

export const getNetworkOperations = async (date, hour) => {
  const response = await api.get("/operations/summary", {
    params: { date, hour },
  });

  return response.data;
};

export const getStationOperations = async (station, date, hour) => {
  const response = await api.get(
    `/operations/stations/${encodeURIComponent(station)}`,
    {
      params: { date, hour },
    }
  );

  return response.data;
};

// ---------------------------------------------------------
// PREDICTIONS
// ---------------------------------------------------------

// Next-calendar-day demand forecast
export const getDemandForecast = async () => {
  const response = await api.get("/prediction/demand");
  return response.data;
};

// Predict next-hour ridership using the latest available
// historical observation for the selected station.
export const getLatestStationPrediction = async (station) => {
  const response = await api.get(
    `/prediction/crowd/latest/${encodeURIComponent(station)}`
  );

  return response.data;
};

// Future hourly forecast from the trained model, rolled forward from the
// latest observation (target must be after the data and within 90 days).
export const getStationHourlyForecast = async (
  station,
  targetDate,
  targetHour
) => {
  const response = await api.get(
    `/prediction/crowd/forecast/${encodeURIComponent(
      station
    )}/${encodeURIComponent(targetDate)}/${encodeURIComponent(targetHour)}`
  );
  return response.data;
};

// ---------------------------------------------------------
// GTFS SCHEDULE DATA
// Scheduled service, not live train tracking
// ---------------------------------------------------------

export const getMetroRoutes = async () => {
  const response = await api.get("/scheduling/routes");
  return response.data;
};

export const getRouteStations = async (routeId) => {
  const response = await api.get(
    `/scheduling/routes/${encodeURIComponent(routeId)}/stations`
  );

  return response.data;
};

export const getRouteTrips = async (routeId) => {
  const response = await api.get(
    `/scheduling/routes/${encodeURIComponent(routeId)}/trips`
  );

  return response.data;
};

export const getRouteFrequency = async (routeId) => {
  const response = await api.get(
    `/scheduling/routes/${encodeURIComponent(routeId)}/frequency`
  );

  return response.data;
};

export const getTripSchedule = async (tripId) => {
  const response = await api.get(
    `/scheduling/trips/${encodeURIComponent(tripId)}/schedule`
  );

  return response.data;
};

// ---------------------------------------------------------
// CROWD INTELLIGENCE
// ---------------------------------------------------------

export const getCrowdStatus = async () => {
  const response = await api.get("/crowd/status");
  return response.data;
};

export const getDemoLiveMonitoring = async () => {
  const response = await api.get("/monitoring/demo-live");
  return response.data;
};

export const getCrowdHotspots = async () => {
  const response = await api.get("/crowd/hotspots");
  return response.data;
};

export const getCrowdFlow = async () => {
  const response = await api.get("/crowd/flow");
  return response.data;
};

export const getCrowdHeatmap = async () => {
  const response = await api.get("/crowd/heatmap");
  return response.data;
};

export const getCrowdDemandPressure = async () => {
  const response = await api.get("/crowd/demand-pressure");
  return response.data;
};

// ---------------------------------------------------------
// HISTORICAL ANALYTICS
// ---------------------------------------------------------

export const getAnalyticsOverview = async () => {
  const response = await api.get("/analytics/overview");
  return response.data;
};

export const getAnalyticsTrends = async () => {
  const response = await api.get("/analytics/trends");
  return response.data;
};

export const getAnalyticsAnomalies = async (limit = 100) => {
  const response = await api.get("/analytics/anomalies", {
    params: { limit },
  });

  return response.data;
};

export const getAnalyticsStations = async (limit = 20) => {
  const response = await api.get("/analytics/stations", {
    params: { limit },
  });

  return response.data;
};

export const getAnalyticsPassengerFlow = async () => {
  const response = await api.get("/analytics/passenger-flow");
  return response.data;
};

export const getAnalyticsHotspots = async (limit = 20) => {
  const response = await api.get("/analytics/hotspots", {
    params: { limit },
  });

  return response.data;
};

export const getAnalyticsModelInsights = async () => {
  const response = await api.get("/analytics/model-insights");
  return response.data;
};

export const getAnalyticsHeatmap = async () => {
  const response = await api.get("/analytics/heatmap");
  return response.data;
};

// ---------------------------------------------------------
// SAVED SCHEDULING PROPOSALS
// ---------------------------------------------------------

export const getFrequencyProposals = async (status) => {
  const response = await api.get("/scheduling/proposals", {
    params: status ? { status } : {},
  });

  return response.data;
};

export const createFrequencyProposal = async (proposal) => {
  const response = await api.post("/scheduling/proposals", proposal);
  return response.data;
};

export const updateFrequencyProposal = async (proposalId, status) => {
  const response = await api.patch(
    `/scheduling/proposals/${proposalId}`,
    { status }
  );

  return response.data;
};

// ---------------------------------------------------------
// FREQUENCY WHAT-IF CALCULATION
// Mathematical comparison of current and proposed headways
// ---------------------------------------------------------

export const getFrequencyWhatIf = async (
  currentHeadway,
  proposedHeadway
) => {
  const response = await api.get("/scheduling/frequency/what-if", {
    params: {
      current_headway_minutes: currentHeadway,
      proposed_headway_minutes: proposedHeadway,
    },
  });

  return response.data;
};

// ---------------------------------------------------------
// ML-BASED FREQUENCY ANALYSIS
// Combines station ridership forecasting with the existing
// analytical scheduling recommendation.
// ---------------------------------------------------------

export const getFrequencyAnalysis = async ({
  station,
  targetDate,
  targetHour,
  currentHeadway,
  proposedHeadway,
}) => {
  const response = await api.get("/scheduling/frequency/analysis", {
    params: {
      station,
      target_date: targetDate,
      target_hour: targetHour,
      current_headway_minutes: currentHeadway,
      proposed_headway_minutes: proposedHeadway,
    },
  });

  return response.data;
};

// ---------------------------------------------------------
// SAVED DELAY RECORDS
// ---------------------------------------------------------

export const getDelayRecords = async (routeId) => {
  const response = await api.get("/scheduling/delays", {
    params: routeId ? { route_id: routeId } : {},
  });

  return response.data;
};

export const createDelayRecord = async (delayRecord) => {
  const response = await api.post("/scheduling/delays", delayRecord);
  return response.data;
};

// ---------------------------------------------------------
// DEFAULT API CLIENT
// ---------------------------------------------------------

export default api;


