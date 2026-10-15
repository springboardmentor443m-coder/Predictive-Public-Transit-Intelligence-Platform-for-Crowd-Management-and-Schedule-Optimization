/**
 * AI MetroFlow - Centralized API Client
 * Interfaces with FastAPI backend at http://127.0.0.1:8000
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || 15000);
    config.signal = controller.signal;

    try {
      const response = await fetch(url, config);
      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData = null;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText };
        }
        const error = new Error(errorData.detail || `Request failed with status ${response.status}`);
        error.status = response.status;
        error.data = errorData;
        throw error;
      }

      return await response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error(`API request timed out after ${options.timeout || 15000}ms: ${url}`);
      }
      throw err;
    }
  }

  /**
   * Health & Telemetry
   */
  async getHealth() {
    return this.request('/health');
  }

  /**
   * Root Service Metadata
   */
  async getRoot() {
    return this.request('/');
  }

  /**
   * Stations Catalog with Predictions
   */
  async getStations({ borough, congestion, hour } = {}) {
    const params = new URLSearchParams();
    if (borough && borough !== 'All') params.append('borough', borough);
    if (congestion && congestion !== 'All') params.append('congestion', congestion);
    if (hour !== undefined && hour !== null) params.append('hour', hour);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return this.request(`/stations${qs}`);
  }

  /**
   * Live Simulated Trains Telemetry
   */
  async getTrains(stepDelta = 3.0) {
    return this.request(`/trains?step_delta=${stepDelta}`);
  }

  /**
   * Delay Injection Simulation
   */
  async injectTrainDelay(trainId, delayMinutes = 5.0) {
    return this.request('/trains/inject-delay', {
      method: 'POST',
      body: JSON.stringify({ train_id: trainId, delay_minutes: delayMinutes }),
    });
  }

  /**
   * Schedule Recommendation for Congestion Tier
   */
  async getScheduleRecommendation(congestionLevel) {
    return this.request(`/schedule-recommendation/${encodeURIComponent(congestionLevel)}`);
  }

  /**
   * Real-Time Single Station Congestion Inference
   */
  async predictCongestion(payload) {
    return this.request('/predict', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Multi-Horizon Demand Forecasting
   */
  async getDemandForecasts(horizon = 'Next 1 Hour') {
    const qs = `?horizon=${encodeURIComponent(horizon)}`;
    return this.request(`/demand-forecasts${qs}`);
  }

  /**
   * Multi-Model Leaderboard & Feature Importances
   */
  async getModelComparison() {
    return this.request('/model-comparison');
  }

  /**
   * Dataset EDA & Diurnal Profiles
   */
  async getDatasetStats() {
    return this.request('/dataset-stats');
  }
}

export const api = new ApiClient(API_BASE_URL);
export default api;
