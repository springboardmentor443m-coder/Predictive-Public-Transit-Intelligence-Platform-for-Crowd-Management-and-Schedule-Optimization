import { useEffect, useState } from "react";
import "./App.css";
import "./theme.css";

const API_ROOT = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const API_BASE = `${API_ROOT}/api/v1`;
const LOGIN_API = `${API_ROOT}/login`;
const REGISTER_API = `${API_ROOT}/register`;

const modules = [
  { id: "overview", icon: "⌂", label: "Overview", eyebrow: "Command center" },
  { id: "monitoring", icon: "◉", label: "Live monitoring", eyebrow: "Crowd intelligence" },
  { id: "trains", icon: "▣", label: "Train status", eyebrow: "Network movement" },
  { id: "schedules", icon: "◷", label: "Schedules", eyebrow: "Service planning" },
  { id: "prediction", icon: "✦", label: "AI prediction", eyebrow: "Demand forecast" },
  { id: "alerts", icon: "!", label: "Alerts", eyebrow: "Operational signals" },
  { id: "analytics", icon: "⌁", label: "Analytics", eyebrow: "Performance insights" },
  { id: "settings", icon: "⚙", label: "Settings", eyebrow: "Platform controls" },
];

const stationFallback = [
  { station_code: 101, station_name: "Central Exchange", line_name: "Blue Line", capacity: 2500, passenger_count: 1840, entries: 920, exits: 640, status: "Watch" },
  { station_code: 102, station_name: "City Square", line_name: "Green Line", capacity: 2200, passenger_count: 1120, entries: 580, exits: 510, status: "Normal" },
  { station_code: 103, station_name: "North Terminal", line_name: "Red Line", capacity: 2800, passenger_count: 760, entries: 390, exits: 430, status: "Normal" },
  { station_code: 104, station_name: "Airport Link", line_name: "Gold Line", capacity: 3000, passenger_count: 2260, entries: 1180, exits: 720, status: "Critical" },
];

export default function App() {
  const [loggedIn, setLoggedIn] = useState(() => Boolean(localStorage.getItem("metroflow_access_token")));
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem("metroflow_access_token") || "");
  const [authMode, setAuthMode] = useState("login");
  const [role, setRole] = useState("Operator");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [registrationMessage, setRegistrationMessage] = useState("");
  const [activeModule, setActiveModule] = useState("overview");
  const [health, setHealth] = useState(null);
  const [stations, setStations] = useState([]);
  const [peakHours, setPeakHours] = useState(null);
  const [operations, setOperations] = useState(null);
  const [adminUsers, setAdminUsers] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [hour, setHour] = useState(8);
  const [dayOfWeek, setDayOfWeek] = useState(1);
  const [lag1h, setLag1h] = useState(1200);
  const [lag2h, setLag2h] = useState(950);
  const [rolling3h, setRolling3h] = useState(1100);
  const [prediction, setPrediction] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const loadDashboardData = async (token) => {
    const authHeaders = { Authorization: `Bearer ${token}` };
    try {
      const responses = await Promise.all([
        fetch(`${API_BASE}/health`, { headers: authHeaders }),
        fetch(`${API_BASE}/stations`, { headers: authHeaders }),
        fetch(`${API_BASE}/analytics/peak-hours`, { headers: authHeaders }),
        fetch(`${API_BASE}/operations/summary`, { headers: authHeaders }),
      ]);
      const healthData = await responses[0].json();
      const stationData = await responses[1].json();
      const peakData = await responses[2].json();
      const operationsData = await responses[3].json();
      if (responses.some((response) => response.status === 401)) {
        localStorage.removeItem("metroflow_access_token");
        setAccessToken("");
        setLoggedIn(false);
        return;
      }
      setHealth(healthData);
      setStations(Array.isArray(stationData) && stationData.length ? stationData : stationFallback);
      setSelectedStation(stationData?.[0] || stationFallback[0]);
      setPeakHours(peakData);
      setOperations(operationsData);
    } catch (error) {
      setStations(stationFallback);
      setSelectedStation(stationFallback[0]);
      console.error("Dashboard data unavailable:", error);
    }
  };

  const refreshOperations = async (token) => {
    try {
      const response = await fetch(`${API_BASE}/operations/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.status === 401) {
        localStorage.removeItem("metroflow_access_token");
        setAccessToken("");
        setLoggedIn(false);
        return;
      }
      if (response.ok) setOperations(await response.json());
    } catch (error) {
      console.error("Operations refresh unavailable:", error);
    }
  };

  const loadAdminUsers = async (token) => {
    const response = await fetch(`${API_BASE}/admin/users`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.ok) setAdminUsers(await response.json());
  };

  useEffect(() => {
    if (accessToken) Promise.resolve().then(() => loadDashboardData(accessToken));
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken) return undefined;
    const refreshTimer = window.setInterval(() => refreshOperations(accessToken), 30000);
    return () => window.clearInterval(refreshTimer);
  }, [accessToken]);

  useEffect(() => {
    if (accessToken && role === "Admin") Promise.resolve().then(() => loadAdminUsers(accessToken));
  }, [accessToken, role]);

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoginError("");
    try {
      const response = await fetch(LOGIN_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.message || data.detail || "Unable to sign in");
      localStorage.setItem("metroflow_access_token", data.access_token);
      setAccessToken(data.access_token);
      setLoggedIn(true);
    } catch (error) {
      setLoginError(error.message || "Unable to connect to MetroFlow");
    }
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    setLoginError("");
    setRegistrationMessage("");
    try {
      const response = await fetch(REGISTER_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.message || data.detail || "Unable to create account");
      setAuthMode("login");
      setRegistrationMessage(data.message);
    } catch (error) {
      setLoginError(error.message || "Unable to create account");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("metroflow_access_token");
    setLoggedIn(false);
    setAccessToken("");
    setEmail("");
    setPassword("");
    setActiveModule("overview");
  };

  const handlePredictAndOptimize = async (event) => {
    event.preventDefault();
    setLoading(true);
    setErrorMsg("");
    try {
      const isWeekend = dayOfWeek >= 5 ? 1 : 0;
      const isPeak = !isWeekend && ((hour >= 7 && hour <= 9) || (hour >= 17 && hour <= 20)) ? 1 : 0;
      const capacity = selectedStation?.capacity || 2500;
      const stationCode = selectedStation?.station_code || 150;
      const predictionResponse = await fetch(`${API_BASE}/predict/demand`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ station_code: stationCode, hour: Number(hour), day_of_week: Number(dayOfWeek), is_weekend: isWeekend, is_peak_hour: isPeak, lag_1h: Number(lag1h), lag_2h: Number(lag2h), rolling_3h: Number(rolling3h), station_capacity: capacity }),
      });
      if (!predictionResponse.ok) throw new Error("Forecast API request failed.");
      const predictionData = await predictionResponse.json();
      setPrediction(predictionData);
      const scheduleResponse = await fetch(`${API_BASE}/schedules/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ station_code: stationCode, predicted_demand: predictionData.predicted_passenger_demand, station_capacity: capacity, current_headway_minutes: 10 }),
      });
      if (!scheduleResponse.ok) throw new Error("Scheduling API request failed.");
      setSchedule(await scheduleResponse.json());
    } catch (error) {
      setErrorMsg(error.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  if (!loggedIn) return <LoginScreen {...{ authMode, email, password, role, loginError, registrationMessage, setAuthMode, setEmail, setPassword, setRole, setLoginError, setRegistrationMessage, handleLogin, handleRegister }} />;

  const active = modules.find((item) => item.id === activeModule) || modules[0];
  const totalCapacity = stations.reduce((sum, station) => sum + Number(station.capacity || 0), 0);
  const totalPassengers = stations.reduce((sum, station) => sum + Number(station.passenger_count || 0), 0);
  const criticalStations = stations.filter((station) => station.status === "Critical" || Number(station.passenger_count) / Number(station.capacity) > 0.8).length;

  return (
    <div className="platform-shell">
      <aside className="sidebar">
        <div className="brand-lockup"><span className="brand-mark">M</span><div><strong>MetroFlow</strong><small>Transit intelligence</small></div></div>
        <div className="sidebar-section-label">Workspace</div>
        <nav className="module-nav" aria-label="Platform modules">
          {modules.map((item) => <button key={item.id} className={activeModule === item.id ? "module-link active" : "module-link"} onClick={() => setActiveModule(item.id)}><span className="module-icon">{item.icon}</span><span>{item.label}</span>{item.id === "alerts" && <b className="nav-count">3</b>}</button>)}
        </nav>
        <div className="sidebar-footer"><div className="secure-note"><span>●</span><div><strong>Network secure</strong><small>All services operational</small></div></div><button className="sidebar-logout" onClick={handleLogout}>Sign out</button></div>
      </aside>

      <main className="workspace">
        <header className="topbar"><div><span className="breadcrumb">MetroFlow / {active.label}</span><h1>{active.eyebrow}</h1></div><div className="topbar-actions"><span className="live-indicator"><i /> Live network</span><span className="date-stamp">Tuesday, 08:45</span><div className="user-chip"><span>{role.slice(0, 1)}</span><div><strong>{role}</strong><small>{email || "operations@metroflow"}</small></div></div></div></header>
        {activeModule === "overview" && <OverviewView {...{ health, stations, peakHours, totalPassengers, totalCapacity, criticalStations, setActiveModule }} />}
        {activeModule === "monitoring" && <MonitoringView stations={stations} />}
        {activeModule === "trains" && <TrainsView operations={operations} />}
        {activeModule === "schedules" && <SchedulesView operations={operations} setActiveModule={setActiveModule} />}
        {activeModule === "prediction" && <PredictionView {...{ stations, selectedStation, setSelectedStation, hour, setHour, dayOfWeek, setDayOfWeek, lag1h, setLag1h, lag2h, setLag2h, rolling3h, setRolling3h, handlePredictAndOptimize, loading, errorMsg, prediction, schedule }} />}
        {activeModule === "alerts" && <AlertsView criticalStations={criticalStations} operations={operations} />}
        {activeModule === "analytics" && <AnalyticsView {...{ peakHours, totalPassengers, stations }} />}
        {activeModule === "settings" && <SettingsView role={role} adminUsers={adminUsers} />}
      </main>
    </div>
  );
}

function LoginScreen({ authMode, email, password, role, loginError, registrationMessage, setAuthMode, setEmail, setPassword, setRole, setLoginError, setRegistrationMessage, handleLogin, handleRegister }) {
  const inputStyle = { marginTop: "7px", padding: "13px 14px", background: "#fff", border: "1px solid #c9d9da", borderRadius: "5px", color: "#18343b" };
  const isRegistering = authMode === "register";
  return <main className="login-screen"><section className="login-split"><div className="login-visual"><div><div className="login-train">🚆</div><p className="login-kicker">METROFLOW</p></div><div><h1>Smarter transit.<br />Better decisions.</h1><p>Predictive intelligence for modern public transportation.</p></div></div><div className="login-form-panel"><p className="login-kicker light">OPERATIONS PORTAL</p><h2>{isRegistering ? "Create an account" : "Welcome back"}</h2><p className="login-intro">{isRegistering ? "Register as a transit operator to access MetroFlow intelligence." : "Sign in to access MetroFlow intelligence."}</p><form onSubmit={isRegistering ? handleRegister : handleLogin}><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required style={inputStyle} /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder={isRegistering ? "At least 8 characters" : "Enter your password"} minLength={isRegistering ? 8 : undefined} required style={inputStyle} /></label>{!isRegistering && <label>Login role<select value={role} onChange={(event) => setRole(event.target.value)} style={inputStyle}><option value="Operator">Operator</option><option value="Admin">Admin</option></select></label>}{registrationMessage && <p className="login-success">{registrationMessage}</p>}{loginError && <p className="login-error">{loginError}</p>}<button className="primary-button" type="submit">{isRegistering ? "Create operator account" : "Login to MetroFlow"}</button></form><button className="auth-switch" type="button" onClick={() => { setAuthMode(isRegistering ? "login" : "register"); setLoginError(""); setRegistrationMessage(""); }}>{isRegistering ? "Already have an account? Sign in" : "New to MetroFlow? Create an account"}</button></div></section></main>;
}

function OverviewView({ health, stations, peakHours, totalPassengers, totalCapacity, criticalStations, setActiveModule }) {
  const occupancy = totalCapacity ? Math.round((totalPassengers / totalCapacity) * 100) : 0;
  return <div className="view-content"><div className="view-heading"><div><span className="section-kicker">Network pulse / 08:45 local</span><h2>Good morning, operator.</h2><p>Here is what is happening across your transit network right now.</p></div><button className="primary-button compact" onClick={() => setActiveModule("prediction")}>Run a forecast <span>→</span></button></div><div className="hero-strip"><div><span className="section-kicker">Network load</span><strong>{occupancy || 68}%</strong><p>Current average occupancy across monitored hubs</p></div><div className="signal-bars"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div><div className="hero-strip-side"><span className="positive">↑ 6.4%</span><small>vs. yesterday</small></div></div><div className="stat-grid"><StatCard label="Monitored hubs" value={stations.length || 12} suffix="active" tone="cyan" icon="⌘" /><StatCard label="Passengers today" value={totalPassengers ? totalPassengers.toLocaleString() : "18,420"} suffix="+8.2%" tone="blue" icon="↗" /><StatCard label="Critical stations" value={criticalStations || 2} suffix="needs attention" tone="coral" icon="!" /><StatCard label="Model confidence" value={health?.metrics?.r2 ? `${(health.metrics.r2 * 100).toFixed(0)}%` : "94%"} suffix="AI confidence" tone="gold" icon="✦" /></div><div className="dashboard-grid"><section className="content-card network-card"><CardHeader title="Station network" meta="Live occupancy" action="View all" onAction={() => setActiveModule("monitoring")} /><div className="station-list">{stations.slice(0, 4).map((station, index) => <StationRow key={station.station_code || index} station={station} />)}</div></section><section className="content-card schedule-card"><CardHeader title="Service outlook" meta="Today" action="Schedules" onAction={() => setActiveModule("schedules")} /><div className="outlook-chart"><div className="chart-y"><span>100%</span><span>50%</span><span>0%</span></div><div className="chart-area"><div className="chart-line" /><div className="chart-dot dot-a" /><div className="chart-dot dot-b" /><div className="chart-dot dot-c" /><div className="chart-dot dot-d" /><div className="chart-labels"><span>06:00</span><span>09:00</span><span>12:00</span><span>18:00</span><span>21:00</span></div></div></div><div className="chart-summary"><span><i className="legend-dot cyan" />Forecast demand</span><strong>{peakHours?.morning_peak ? `${peakHours.morning_peak.hour}:00 peak` : "08:00 peak"}</strong></div></section></div><section className="content-card activity-card"><CardHeader title="Latest activity" meta="Just now" action="Open alerts" onAction={() => setActiveModule("alerts")} /><div className="activity-list"><Activity time="08:42" title="Demand forecast completed" detail="Central Exchange · next 60 minutes" type="success" /><Activity time="08:37" title="Headway recommendation issued" detail="Gold Line · reduce to 5 minutes" type="info" /><Activity time="08:31" title="Platform load rising" detail="Airport Link · 82% occupied" type="warning" /></div></section></div>;
}

function StatCard({ label, value, suffix, tone, icon }) { return <div className={`stat-card ${tone}`}><span className="stat-icon">{icon}</span><div><span className="stat-label">{label}</span><strong>{value}</strong><small>{suffix}</small></div></div>; }
function CardHeader({ title, meta, action, onAction }) { return <div className="card-header"><div><h3>{title}</h3><span>{meta}</span></div>{action && <button onClick={onAction}>{action} <b>↗</b></button>}</div>; }
function StationRow({ station }) { const load = Math.min(100, Math.round((Number(station.passenger_count || 0) / Number(station.capacity || 2500)) * 100)); const status = load > 80 ? "Critical" : load > 60 ? "Watch" : "Normal"; return <div className="station-row"><span className="station-marker">{load > 80 ? "!" : "•"}</span><div className="station-name"><strong>{station.station_name}</strong><small>{station.line_name || "Network hub"}</small></div><div className="load-meter"><span><i style={{ width: `${load || 42}%` }} /></span><small>{load || 42}%</small></div><em className={`status-tag ${status.toLowerCase()}`}>{status}</em></div>; }
function Activity({ time, title, detail, type }) { return <div className="activity-row"><time>{time}</time><span className={`activity-dot ${type}`} /><div><strong>{title}</strong><small>{detail}</small></div><button>•••</button></div>; }

function MonitoringView({ stations }) { return <div className="view-content"><div className="view-heading"><div><span className="section-kicker">Crowd intelligence / live</span><h2>Live station monitoring</h2><p>Watch passenger density and operational pressure across the network.</p></div><span className="live-indicator large"><i /> Data streaming</span></div><div className="monitor-grid">{(stations.length ? stations : stationFallback).map((station, index) => <div className="monitor-card" key={station.station_code || index}><div className="monitor-card-top"><span className="station-marker">◉</span><span className={`status-tag ${index === 3 ? "critical" : index === 0 ? "watch" : "normal"}`}>{index === 3 ? "Critical" : index === 0 ? "Watch" : "Normal"}</span></div><h3>{station.station_name}</h3><p>{station.line_name || "Network hub"}</p><strong>{Math.round((station.passenger_count || 980)).toLocaleString()}</strong><small>passengers on platform</small><div className="load-meter wide"><span><i style={{ width: `${Math.min(100, ((station.passenger_count || 980) / (station.capacity || 2500)) * 100)}%` }} /></span><small>{Math.min(100, Math.round(((station.passenger_count || 980) / (station.capacity || 2500)) * 100))}%</small></div></div>)}</div></div>; }
function TrainsView({ operations }) { const trains = operations?.trains || []; return <div className="view-content"><ViewTitle kicker="Network movement / fleet" title="Train status" copy="Track every active service and keep the network moving." /><section className="content-card table-card"><div className="table-toolbar"><span>Active services <b>{operations?.active_services || 0}</b></span><button className="filter-button">All lines⌄</button><button className="filter-button">Export ↗</button></div><div className="data-table"><div className="table-head"><span>Service</span><span>Line</span><span>Current station</span><span>Status</span><span>Next arrival</span></div>{trains.map((train) => <div className="table-row" key={train.service}><strong>{train.service}</strong><span>{train.line}</span><span>{train.current_station}</span><em className={train.status === "Delayed" ? "delayed" : "on-time"}>{train.status}</em><span>{train.next_arrival}</span></div>)}</div></section></div>; }
function SchedulesView({ operations, setActiveModule }) { const recommendation = operations?.schedule; return <div className="view-content"><ViewTitle kicker="Service planning / today" title="Schedule control" copy="Coordinate frequency, headway, and reserve capacity before demand arrives." action={<button className="primary-button compact" onClick={() => setActiveModule("prediction")}>Optimize with AI →</button>} /><div className="schedule-layout"><section className="content-card timetable-card"><CardHeader title="Line timetable" meta="Live network" action="Edit" /><div className="time-rail"><span>06:00</span><span>09:00</span><span>12:00</span><span>15:00</span><span>18:00</span><span>21:00</span></div>{[ ["Blue Line", "BL", "#69e0d0"], ["Green Line", "GL", "#8cb9ff"], ["Gold Line", "GD", "#f6c86e"], ["Red Line", "RD", "#ff9278"]].map((line) => <div className="line-row" key={line[0]}><span><i style={{ background: line[2] }}>{line[1]}</i>{line[0]}</span><div><b style={{ left: "18%", background: line[2] }} /><b style={{ left: "43%", background: line[2] }} /><b style={{ left: "72%", background: line[2] }} /></div></div>)}</section><section className="content-card recommendation-card"><span className="section-kicker">AI recommendation</span><h3>Peak window adjustment</h3><strong>Every {recommendation?.recommended_headway_minutes || 0} minutes</strong><p>Increase {recommendation?.line || "network"} frequency around {recommendation?.station || "the busiest station"} to absorb current demand.</p><span className="recommendation-footer">Confidence <b>{recommendation?.confidence || 0}%</b></span></section></div></div>; }
function PredictionView(props) { return <div className="view-content"><ViewTitle kicker="Demand forecast / model v2" title="AI prediction studio" copy="Test future demand scenarios and generate an operational response." /><div className="prediction-layout"><section className="content-card prediction-form"><CardHeader title="Scenario inputs" meta="Required fields" /><form onSubmit={props.handlePredictAndOptimize}><label>Target station<select value={props.selectedStation?.station_code || ""} onChange={(event) => props.setSelectedStation(props.stations.find((station) => station.station_code === Number(event.target.value)))}>{props.stations.map((station) => <option key={station.station_code} value={station.station_code}>{station.station_name}</option>)}</select></label><div className="input-pair"><label>Hour<input type="number" min="0" max="23" value={props.hour} onChange={(event) => props.setHour(event.target.value)} /></label><label>Day<select value={props.dayOfWeek} onChange={(event) => props.setDayOfWeek(event.target.value)}><option value="0">Monday</option><option value="1">Tuesday</option><option value="2">Wednesday</option><option value="3">Thursday</option><option value="4">Friday</option><option value="5">Saturday</option><option value="6">Sunday</option></select></label></div><div className="input-pair"><label>Demand t-1<input type="number" value={props.lag1h} onChange={(event) => props.setLag1h(event.target.value)} /></label><label>Demand t-2<input type="number" value={props.lag2h} onChange={(event) => props.setLag2h(event.target.value)} /></label></div><label>Rolling 3-hour mean<input type="number" value={props.rolling3h} onChange={(event) => props.setRolling3h(event.target.value)} /></label>{props.errorMsg && <p className="error-text">{props.errorMsg}</p>}<button className="primary-button full" disabled={props.loading}>{props.loading ? "Computing..." : "Generate forecast →"}</button></form></section><section className="content-card prediction-result"><span className="section-kicker">Output / dispatch guidance</span>{props.prediction && props.schedule ? <><div className="prediction-number"><span>Predicted demand</span><strong>{props.prediction.predicted_passenger_demand.toLocaleString()}</strong><small>passengers per hour</small></div><div className="prediction-progress"><div style={{ width: `${props.prediction.occupancy_rate * 100}%` }} /></div><div className="prediction-details"><div><span>Occupancy</span><strong>{(props.prediction.occupancy_rate * 100).toFixed(1)}%</strong></div><div><span>Crowd level</span><strong>{props.prediction.crowd_level}</strong></div><div><span>Recommended</span><strong>{props.schedule.recommended_headway_minutes} min headway</strong></div></div><p className="rationale">{props.schedule.rationale}</p></> : <div className="empty-state"><span>✦</span><h3>Ready for a scenario</h3><p>Enter operating conditions to activate the prediction engine.</p></div>}</section></div></div>; }
function AlertsView({ criticalStations, operations }) { const alerts = operations?.alerts || []; return <div className="view-content"><ViewTitle kicker="Operational signals / priority" title="Alerts center" copy="Resolve the issues that need a human decision first." /><div className="alert-summary"><div><strong>{alerts.length || criticalStations}</strong><span>Active incidents</span></div><div><strong>7</strong><span>Resolved today</span></div><div><strong>12m</strong><span>Avg. response</span></div></div><section className="content-card alert-list">{alerts.map((alert, index) => <AlertItem key={`${alert.type}-${index}`} {...alert} />)}</section></div>; }
function AlertItem({ type, title, detail, time, action }) { return <div className="alert-item"><span className={`alert-icon ${type}`}>{type === "critical" ? "!" : type === "warning" ? "△" : "i"}</span><div><strong>{title}</strong><p>{detail}</p><small>{time}</small></div><button>{action} →</button></div>; }
function AnalyticsView({ peakHours, totalPassengers, stations }) { return <div className="view-content"><ViewTitle kicker="Performance insights / historical" title="Network analytics" copy="Turn passenger movement into decisions your team can act on." /><div className="analytics-grid"><section className="content-card big-chart"><CardHeader title="Passenger volume" meta="Last 7 days" action="Download" /><div className="bar-chart">{[42, 58, 51, 74, 68, 88, 79, 94, 82, 96, 75, 84].map((height, index) => <span key={index} style={{ height: `${height}%` }} className={index > 8 ? "today" : ""} />)}</div><div className="chart-days"><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span></div></section><section className="content-card insight-card"><span className="section-kicker">At a glance</span><h3>Peak behavior</h3><div className="insight-stat"><span>Morning rush</span><strong>{peakHours?.morning_peak ? `${peakHours.morning_peak.hour}:00` : "08:00"}</strong></div><div className="insight-stat"><span>Evening rush</span><strong>{peakHours?.evening_peak ? `${peakHours.evening_peak.hour}:00` : "18:00"}</strong></div><div className="insight-stat"><span>Data coverage</span><strong>{stations.length || 12} hubs</strong></div><p>Passenger volume is trending above the weekly baseline. Keep reserve capacity ready for the evening window.</p></section></div><div className="insight-banner"><span>✦</span><div><strong>Model insight</strong><p>{totalPassengers ? `${totalPassengers.toLocaleString()} passengers are currently represented in the live network view.` : "Live network volume is ready for analysis."}</p></div></div></div>; }
function SettingsView({ role, adminUsers }) { return <div className="view-content"><ViewTitle kicker="Platform controls / access" title="Settings" copy="Manage the operational preferences for this workspace." /><div className="settings-grid"><section className="content-card settings-card"><CardHeader title="Workspace profile" meta="Current session" /><label>Workspace name<input value="MetroFlow Control Center" readOnly /></label><label>Default role<select value={role} readOnly onChange={() => {}}><option>{role}</option></select></label><label>Time zone<select value="Local network time" readOnly onChange={() => {}}><option>Local network time</option></select></label><button className="primary-button">Save preferences</button></section><section className="content-card settings-card"><CardHeader title="Connected services" meta="Architecture layer" /><Service name="Data & storage" status="Connected" /><Service name="Prediction engine" status="Connected" /><Service name="Alerts gateway" status="Connected" /><Service name="External integrations" status="Standby" /></section>{role === "Admin" && <section className="content-card settings-card"><CardHeader title="User access" meta={`${adminUsers.length} accounts`} />{adminUsers.map((user) => <div className="service-row" key={user.email}><span className="service-dot" /><div><strong>{user.email}</strong><small>MetroFlow account</small></div><em>{user.role}</em></div>)}</section>}</div></div>; }
function Service({ name, status }) { return <div className="service-row"><span className="service-dot" /><div><strong>{name}</strong><small>MetroFlow platform service</small></div><em>{status}</em></div>; }
function ViewTitle({ kicker, title, copy, action }) { return <div className="view-heading"><div><span className="section-kicker">{kicker}</span><h2>{title}</h2><p>{copy}</p></div>{action}</div>; }
