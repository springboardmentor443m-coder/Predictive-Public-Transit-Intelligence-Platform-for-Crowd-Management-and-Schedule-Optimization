const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/^http/, 'ws');

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export function liveSocketUrl() {
  return `${WS_BASE_URL}/ws/live`;
}

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/`, { method: 'GET', headers: { 'Content-Type': 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend health check failed, running with local intelligence mode:", err);
    return { status: "Offline", error: err.message };
  }
}

export async function fetchMetadata() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/meta`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Using fallback metadata due to error:", err);
    return null;
  }
}

export async function predictOccupancy(params) {
  try {
    const payload = {
      entry_hour: Number(params.entry_hour),
      day_of_week: Number(params.day_of_week),
      from_station: Number(params.from_station),
      to_station: Number(params.to_station),
      line_color: Number(params.line_color),
      train_capacity: Number(params.train_capacity)
    };

    const res = await fetch(`${API_BASE_URL}/api/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Prediction API Error ${res.status}: ${errorText}`);
    }

    return await res.json();
  } catch (err) {
    console.error("Prediction API failed:", err);
    // Fallback calculation in case backend is disconnected
    const hour = Number(params.entry_hour);
    const isPeak = (hour >= 8 && hour <= 11) || (hour >= 17 && hour <= 20);
    const basePax = isPeak ? 1650 + Math.floor(Math.sin(hour) * 150) : (hour >= 12 && hour <= 16 ? 850 : 330);
    const capacity = Number(params.train_capacity) || 2400;
    
    let tier = "OFF_PEAK";
    let headway = 10;
    let action = "Extend Headway to 10 Minutes (Conserve Fleet)";
    let alertMsg = "Off-Peak flow within normal limits.";
    let alertLevel = "NORMAL";
    
    if (basePax >= 1500) {
      tier = "SEVERE_RUSH";
      headway = 3;
      action = "Reduce Headway to 3 Minutes (High-Frequency Dispatch)";
      alertMsg = `🚨 Overcrowding Alert: Projected ${basePax} passengers (${Math.round(basePax/capacity*100)}% capacity). High-frequency fleet dispatch activated.`;
      alertLevel = "CRITICAL_OVERCROWDING";
    } else if (basePax >= 800) {
      tier = "MODERATE_TRAFFIC";
      headway = 6;
      action = "Maintain Standard Headway (5-6 Minutes)";
      alertMsg = `🟡 Moderate Traffic: Projected ${basePax} passengers. Standard headway.`;
      alertLevel = "MODERATE_CONGESTION";
    }

    return {
      predicted_occupancy: basePax,
      predicted_occupancy_int: basePax,
      train_capacity: capacity,
      occupancy_rate_pct: Math.round((basePax / capacity) * 100),
      is_peak_hour: isPeak,
      entry_hour_formatted: `${hour.toString().padStart(2, '0')}:00`,
      recommended_headway_min: headway,
      fleet_action: action,
      alert_status: {
        alert_level: alertLevel,
        tier: tier,
        is_emergency: alertLevel === "CRITICAL_OVERCROWDING",
        occupancy_rate_pct: Math.round((basePax / capacity) * 100),
        message: alertMsg,
        recommended_action: action,
        channels_notified: ["Local Dashboard Fallback"]
      }
    };
  }
}

export async function fetchScheduleAdvisory() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/schedule-advisory`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Schedule advisory fetch failed, using built-in reference list:", err);
    return null;
  }
}

export async function fetchAnalytics() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/analytics`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Analytics fetch failed, using calculated metrics:", err);
    return null;
  }
}

/* ------------------------------------------------------------------ *
 * Live operations: crowd streaming, timetable, delay propagation, ML
 * ------------------------------------------------------------------ */

export async function fetchLiveNetwork() {
  return request('/api/live/network');
}

export async function fetchLiveSnapshot() {
  return request('/api/live/snapshot');
}

export async function fetchLiveStation(station) {
  return request(`/api/live/station/${encodeURIComponent(station)}`);
}

export async function fetchTimetable(line, limit = 200) {
  const q = new URLSearchParams({ limit: String(limit) });
  if (line) q.append('line', line);
  return request(`/api/schedule/timetable?${q}`);
}

export async function fetchDelayTable(limit = 200) {
  return request(`/api/schedule/delays?limit=${limit}`);
}

export async function fetchStationDelays(station) {
  return request(`/api/schedule/station/${encodeURIComponent(station)}`);
}

export async function injectDelay(trainId, station, minutes) {
  return request('/api/schedule/inject-delay', {
    method: 'POST',
    body: JSON.stringify({
      train_id: trainId,
      station,
      minutes: Number(minutes),
    }),
  });
}

export async function clearDelay(trainId) {
  return request(`/api/schedule/clear-delay/${encodeURIComponent(trainId)}`, {
    method: 'POST',
  });
}

export async function resetDelays() {
  return request('/api/schedule/reset', { method: 'POST' });
}

export async function simulateClock(minutes = 60) {
  return request(`/api/schedule/simulate?minutes=${minutes}`, { method: 'POST' });
}

export async function fetchMLMetrics() {
  return request('/api/ml/metrics');
}

export async function fetchMLImportances() {
  return request('/api/ml/importances');
}
