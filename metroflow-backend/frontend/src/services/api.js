const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

    let rakeCap = 1500;
    let rakeFormation = "4-Coach (1,500 pax) Standard Feeder Rake";
    let rakeDesc = "4-coach feeder rake formation is optimal for off-peak passenger volume, minimizing idle coach power and fleet wear.";
    if (basePax >= 1500) {
      rakeCap = 2400;
      rakeFormation = "8-Coach (2,400 pax) High-Capacity Heavy Metro Rake";
      rakeDesc = "High-density crowd requires maximum 8-coach rake formation to prevent platform overcrowding and maintain safety margins.";
    } else if (basePax >= 800) {
      rakeCap = 1800;
      rakeFormation = "6-Coach (1,800 pax) Standard Mainline Rake";
      rakeDesc = "Standard 6-coach mainline rake provides optimal passenger comfort and energy efficiency for moderate flow.";
    }

    return {
      predicted_occupancy: basePax,
      predicted_occupancy_int: basePax,
      train_capacity: capacity,
      occupancy_rate_pct: Math.round((basePax / capacity) * 100),
      is_peak_hour: isPeak,
      entry_hour_formatted: `${hour.toString().padStart(2, '0')}:00`,
      recommended_headway_min: headway,
      recommended_rake_capacity: rakeCap,
      recommended_rake_formation: rakeFormation,
      recommended_rake_desc: rakeDesc,
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

export async function fetchScheduleAdvisory(from_station, to_station, line, hour) {
  const params = new URLSearchParams();
  if (from_station) params.set('from_station', from_station);
  if (to_station) params.set('to_station', to_station);
  if (line) params.set('line', line);
  if (hour) params.set('hour', hour);
  const query = params.toString() ? `?${params.toString()}` : '';
  try {
    const res = await fetch(`${API_BASE_URL}/api/schedule-advisory${query}`);
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
