import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  getDemandForecast,
  getLatestStationPrediction,
  getNetworkScheduling,
} from "../services/api";

const C = {
  page: "#070d18",
  panel: "#17263b",
  border: "rgba(100,190,255,.28)",
  text: "#f1f7ff",
  muted: "#b0c1d8",
  cyan: "#38d9ff",
  purple: "#c4a7ff",
  green: "#5ee6a8",
  orange: "#ffd166",
  red: "#ff8295",
};

const numberFormat = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });
const fmt = (value) => {
  if (value === null || value === undefined || value === "") return "—";
  const n = Number(value);
  return Number.isFinite(n) ? numberFormat.format(n) : "—";
};
const date = (value) => {
  if (!value) return "—";
  const parts = String(value).split("-");
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : String(value);
};
const firstValue = (object, keys, fallback = null) => {
  if (!object) return fallback;
  for (const key of keys) {
    if (object[key] !== undefined && object[key] !== null) return object[key];
  }
  return fallback;
};
const arrayFrom = (value, keys = []) => {
  if (Array.isArray(value)) return value;
  if (!value || typeof value !== "object") return [];
  for (const key of keys) if (Array.isArray(value[key])) return value[key];
  return [];
};
const getError = (error, fallback) =>
  error?.response?.data?.detail || error?.response?.data?.message || error?.message || fallback;
const stationName = (row) => String(firstValue(row, ["station", "Station", "station_name", "name"], "Unknown station"));
const priorityTone = (priority) => {
  const value = String(priority || "").toUpperCase();
  if (value === "HIGH") return "red";
  if (value === "MODERATE") return "orange";
  if (value === "LOW") return "green";
  return "cyan";
};

const panel = {
  background: "linear-gradient(145deg,#1b2d45,#142238)",
  color: C.text,
  border: `1px solid ${C.border}`,
  borderRadius: 15,
  padding: 20,
  minWidth: 0,
  boxShadow: "0 10px 26px rgba(0,0,0,.18)",
};
const labelStyle = {
  color: C.muted,
  fontSize: 11,
  fontWeight: 800,
  letterSpacing: ".1em",
  textTransform: "uppercase",
};
const bodyText = { color: C.muted, fontSize: 13, lineHeight: 1.7 };
const grid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit,minmax(min(100%,190px),1fr))",
  gap: 13,
};
const buttonStyle = {
  background: "rgba(56,217,255,.1)",
  color: C.cyan,
  border: "1px solid rgba(56,217,255,.3)",
  borderRadius: 9,
  padding: "10px 14px",
  fontWeight: 800,
  fontSize: 12,
  cursor: "pointer",
};
const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  background: "#081321",
  color: C.text,
  border: `1px solid ${C.border}`,
  borderRadius: 9,
  padding: "11px 12px",
  fontSize: 13,
  outlineColor: C.cyan,
};

function Pill({ children, tone = "cyan" }) {
  const color = C[tone] || C.cyan;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", border: `1px solid ${color}55`, background: `${color}12`, color, borderRadius: 999, padding: "5px 9px", fontSize: 11, fontWeight: 800, overflowWrap: "anywhere" }}>
      {children}
    </span>
  );
}
function SectionHeading({ index, eyebrow, title, description }) {
  return (
    <div style={{ display: "flex", gap: 13, marginBottom: 16 }}>
      <div style={{ flex: "0 0 36px", width: 36, height: 36, display: "grid", placeItems: "center", borderRadius: 10, background: "rgba(56,217,255,.09)", color: C.cyan, border: `1px solid ${C.border}`, fontWeight: 900, fontSize: 12 }}>{index}</div>
      <div style={{ minWidth: 0 }}>
        <div style={labelStyle}>{eyebrow}</div>
        <h2 style={{ color: C.text, fontSize: "clamp(19px,2.2vw,23px)", margin: "5px 0", letterSpacing: "-.025em" }}>{title}</h2>
        <p style={{ ...bodyText, margin: 0 }}>{description}</p>
      </div>
    </div>
  );
}
function StatCard({ title, value, detail, accent = "cyan" }) {
  const color = C[accent] || C.cyan;
  return (
    <div style={{ ...panel, padding: 17, position: "relative", overflow: "hidden" }}>
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 3, background: color }} />
      <div style={labelStyle}>{title}</div>
      <div style={{ color: C.text, fontSize: "clamp(22px,2.8vw,29px)", fontWeight: 900, marginTop: 11, overflowWrap: "anywhere" }}>{value}</div>
      <div style={{ ...bodyText, fontSize: 12, marginTop: 6 }}>{detail}</div>
    </div>
  );
}
function ErrorMessage({ children }) {
  if (!children) return null;
  return <div role="alert" style={{ color: "#fda4af", background: "rgba(251,113,133,.08)", border: "1px solid rgba(251,113,133,.3)", borderRadius: 10, padding: 12, margin: "10px 0", fontSize: 13, overflowWrap: "anywhere" }}>{children}</div>;
}
function LoadingPanel({ children = "Loading data…" }) {
  return <div style={{ ...panel, ...bodyText }} role="status">{children}</div>;
}
function Notice({ title, children, tone = "orange" }) {
  const color = C[tone] || C.orange;
  return <div style={{ border: `1px solid ${color}45`, background: `${color}09`, borderRadius: 11, padding: 14, marginTop: 13, ...bodyText }}><strong style={{ color }}>{title}</strong><div style={{ marginTop: 5 }}>{children}</div></div>;
}
function DataTable({ columns, rows, emptyText = "No records returned." }) {
  if (!rows.length) return <div style={{ ...panel, ...bodyText }}>{emptyText}</div>;
  return (
    <div style={{ ...panel, overflowX: "auto", padding: 12 }}>
      <table style={{ width: "100%", minWidth: 570, borderCollapse: "collapse", fontSize: 12 }}>
        <thead><tr style={{ textAlign: "left", color: C.muted }}>{columns.map((column) => <th key={column.key} style={{ padding: 11, borderBottom: `1px solid ${C.border}`, whiteSpace: "nowrap" }}>{column.label}</th>)}</tr></thead>
        <tbody>{rows.map((row, index) => <tr key={`${stationName(row)}-${index}`}>{columns.map((column) => <td key={column.key} style={{ padding: 11, borderBottom: `1px solid ${C.border}`, verticalAlign: "top", overflowWrap: "anywhere" }}>{column.render ? column.render(row, index) : fmt(firstValue(row, [column.key]))}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

export default function AIPredictions() {
  const [forecast, setForecast] = useState(null);
  const [forecastLoading, setForecastLoading] = useState(true);
  const [forecastError, setForecastError] = useState("");

  const [station, setStation] = useState("Mahatma Gandhi Road");
  const [stationResult, setStationResult] = useState(null);
  const [stationLoading, setStationLoading] = useState(false);
  const [stationError, setStationError] = useState("");

  const [schedulingData, setSchedulingData] = useState(null);
  const [schedulingLoading, setSchedulingLoading] = useState(true);
  const [schedulingError, setSchedulingError] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("ALL");

  const loadForecast = useCallback(async () => {
    setForecastLoading(true);
    setForecastError("");
    try {
      setForecast(await getDemandForecast());
    } catch (error) {
      setForecast(null);
      setForecastError(getError(error, "Unable to load the demand forecast."));
    } finally {
      setForecastLoading(false);
    }
  }, []);

  const loadScheduling = useCallback(async () => {
    setSchedulingLoading(true);
    setSchedulingError("");
    try {
      setSchedulingData(await getNetworkScheduling());
    } catch (error) {
      setSchedulingData(null);
      setSchedulingError(getError(error, "Unable to load scheduling recommendations."));
    } finally {
      setSchedulingLoading(false);
    }
  }, []);

  const refreshAll = useCallback(() => {
    loadForecast();
    loadScheduling();
  }, [loadForecast, loadScheduling]);

  useEffect(() => { refreshAll(); }, [refreshAll]);

  const runStationPrediction = async (event) => {
    event.preventDefault();
    const name = station.trim();
    if (!name) {
      setStationError("Please enter a station name.");
      setStationResult(null);
      return;
    }
    setStationLoading(true);
    setStationError("");
    setStationResult(null);
    try {
      const result = await getLatestStationPrediction(name);
      const prediction = firstValue(result, ["predicted_next_hour_ridership", "prediction", "predicted_ridership"]);
      if (result?.message && (prediction === null || prediction === undefined || prediction === "")) {
        setStationError(result.message);
      } else {
        setStationResult(result);
      }
    } catch (error) {
      setStationError(getError(error, "Unable to generate the station prediction."));
    } finally {
      setStationLoading(false);
    }
  };

  const stale = forecast?.is_stale === true || forecast?.freshness_status === "stale_historical_data";
  const recommendations = useMemo(() => arrayFrom(schedulingData?.recommendations, ["data", "results"]), [schedulingData]);
  const filteredRecommendations = useMemo(() => recommendations.filter((row) => priorityFilter === "ALL" || String(row.priority_level || "").toUpperCase() === priorityFilter), [recommendations, priorityFilter]);
  const refreshing = forecastLoading || schedulingLoading;

  return (
    <main style={{ minHeight: "100%", boxSizing: "border-box", padding: "clamp(16px,3vw,32px)", color: C.text, background: `radial-gradient(ellipse at 8% 0%,rgba(55,215,245,.08),transparent 32%), radial-gradient(ellipse at 94% 8%,rgba(167,139,250,.08),transparent 30%), ${C.page}`, fontFamily: "inherit" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 18, flexWrap: "wrap", marginBottom: 22, padding: "22px clamp(17px,3vw,28px)", border: `1px solid ${C.border}`, borderRadius: 17, background: "linear-gradient(115deg,rgba(15,29,48,.98),rgba(10,20,35,.96))" }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ ...labelStyle, color: C.cyan, marginBottom: 8 }}>AI METROFLOW / PREDICTIVE INTELLIGENCE</div>
          <h1 style={{ fontSize: "clamp(27px,4vw,37px)", letterSpacing: "-.04em", margin: 0 }}>AI Predictions</h1>
          <p style={{ ...bodyText, margin: "8px 0 0", maxWidth: 700 }}>Forecast network demand, estimate next-hour station ridership, and review data-driven service-frequency recommendations.</p>
        </div>
        <button type="button" onClick={refreshAll} disabled={refreshing} style={{ ...buttonStyle, opacity: refreshing ? 0.65 : 1 }}>{refreshing ? "Refreshing…" : "↻ Refresh predictions"}</button>
      </header>

      {/* 01 — Next-day network-wide demand forecast */}
      <section style={{ marginTop: 28, marginBottom: 34 }}>
        <SectionHeading index="01" eyebrow="Network forecast" title="Next-Day Demand Forecast" description="Estimated total ridership for the next calendar day from the existing XGBoost demand model." />
        <ErrorMessage>{forecastError}</ErrorMessage>
        {forecastLoading ? <LoadingPanel>Loading next-day demand forecast…</LoadingPanel> : forecast ? <>
          <div style={grid}>
            <StatCard title="Predicted ridership" value={fmt(forecast.predicted_ridership)} detail={`${forecast.unit || "passengers"} · model estimate`} accent="cyan" />
            <StatCard title="Forecast date" value={date(forecast.forecast_date)} detail="Target date returned by the model" accent="purple" />
            <StatCard title="Latest observed ridership" value={fmt(forecast.latest_observed_ridership)} detail={`Observed date: ${date(forecast.latest_observed_date)}`} accent="green" />
            <StatCard title="Data freshness" value={stale ? "Stale data" : forecast.freshness_status === "future_dated_observation" ? "Future-dated" : forecast.freshness_status === "recent_historical_data" ? "Recent data" : "Unconfirmed"} detail={forecast.data_age_days === undefined ? "Observation age not provided by API" : `Observation age: ${forecast.data_age_days} day(s)`} accent={stale ? "orange" : "green"} />
          </div>
          <div style={{ ...panel, marginTop: 13 }}>
            <div style={labelStyle}>Model details</div>
            <div style={{ fontWeight: 800, marginTop: 7 }}>{forecast.model || "XGBoost"} {forecast.model_version || ""}</div>
            {forecast.note && <p style={bodyText}>{forecast.note}</p>}
            <div style={{ marginTop: 10 }}><Pill tone={stale ? "orange" : "cyan"}>{forecast.freshness_status || "Freshness status unavailable"}</Pill></div>
          </div>
        </> : <div style={panel}>No forecast data was returned by the backend.</div>}
      </section>

      {/* 02 — Station-level next-hour prediction */}
      <section style={{ marginBottom: 34 }}>
        <SectionHeading index="02" eyebrow="Station intelligence" title="Next-Hour Station Prediction" description="Run the trained model using the latest available historical observation for the selected station." />
        <form onSubmit={runStationPrediction} style={{ ...panel, display: "flex", alignItems: "end", gap: 12, flexWrap: "wrap" }}>
          <label style={{ flex: "1 1 260px" }}>
            <span style={{ ...labelStyle, display: "block", marginBottom: 8 }}>Station name</span>
            <input value={station} onChange={(event) => setStation(event.target.value)} placeholder="Enter a station name" maxLength={150} style={inputStyle} />
          </label>
          <button type="submit" disabled={stationLoading} style={{ ...buttonStyle, opacity: stationLoading ? 0.65 : 1 }}>{stationLoading ? "Predicting…" : "Run prediction →"}</button>
        </form>
        <ErrorMessage>{stationError}</ErrorMessage>
        {stationLoading && <div style={{ marginTop: 12 }}><LoadingPanel>Generating station prediction…</LoadingPanel></div>}
        {stationResult && !stationLoading && <div style={{ ...panel, marginTop: 13 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap", alignItems: "center" }}><h3 style={{ margin: 0 }}>Prediction result</h3><Pill>Estimate · not a live count</Pill></div>
          <div style={{ ...grid, marginTop: 14 }}>
            <StatCard title="Station" value={stationResult.station || station} detail="Station returned by the API" accent="cyan" />
            <StatCard title="Predicted next-hour ridership" value={fmt(firstValue(stationResult, ["predicted_next_hour_ridership", "prediction", "predicted_ridership"]))} detail={`${stationResult.unit || "passengers"} · estimated`} accent="purple" />
            <StatCard title="Latest observation date" value={date(firstValue(stationResult, ["latest_date", "observation_date", "date"]))} detail={`Observation hour: ${firstValue(stationResult, ["latest_hour", "observation_hour", "hour"]) == null ? "—" : `${String(firstValue(stationResult, ["latest_hour", "observation_hour", "hour"])).padStart(2, "0")}:00`}`} accent="green" />
          </div>
          <p style={{ ...bodyText, marginBottom: 0 }}>{stationResult.prediction_note || stationResult.note || "This is a model-generated estimate based on historical data, not a live passenger count."}</p>
        </div>}
        {!stationResult && !stationLoading && !stationError && <p style={{ ...bodyText, marginTop: 12 }}>Choose a station and run a prediction to see its estimate and source observation.</p>}
      </section>

      {/* 03 — Analytical headway recommendations */}
      <section style={{ marginBottom: 34 }}>
        <SectionHeading index="03" eyebrow="Decision support" title="Smart Scheduling Recommendations" description="Compare existing headway patterns with analytical suggestions derived from available demand indicators." />
        <ErrorMessage>{schedulingError}</ErrorMessage>
        <div style={{ ...panel, marginBottom: 13, display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <div><div style={labelStyle}>Network scheduling assessment</div><div style={{ fontWeight: 800, marginTop: 7 }}>{fmt(firstValue(schedulingData, ["total_stations"], recommendations.length))} stations assessed</div><p style={{ ...bodyText, margin: "5px 0 0" }}>Recommendations are advisory; they do not update official metro timetables.</p></div>
          <label style={{ minWidth: 175 }}><span style={{ ...labelStyle, display: "block", marginBottom: 6 }}>Priority filter</span><select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value)} style={inputStyle}><option value="ALL">All priorities</option><option value="HIGH">High priority</option><option value="MODERATE">Moderate priority</option><option value="LOW">Low priority</option></select></label>
        </div>
        {schedulingLoading ? <LoadingPanel>Loading scheduling recommendations…</LoadingPanel> : <DataTable rows={filteredRecommendations} emptyText="No recommendations matched this priority filter." columns={[
          { key: "station", label: "Station", render: (row) => stationName(row) },
          { key: "priority_level", label: "Priority", render: (row) => <Pill tone={priorityTone(row.priority_level)}>{row.priority_level || "UNRATED"}</Pill> },
          { key: "scheduling_priority_score", label: "Priority score", render: (row) => fmt(row.scheduling_priority_score) },
          { key: "current_peak_median_headway_minutes", label: "Current headway (min)", render: (row) => fmt(row.current_peak_median_headway_minutes) },
          { key: "recommended_peak_headway_minutes", label: "Suggested headway (min)", render: (row) => fmt(row.recommended_peak_headway_minutes) },
          { key: "action", label: "Suggested action", render: (row) => row.action || "Review station demand and service gap" },
        ]} />}
        {schedulingData?.assessment_type && <p style={{ ...bodyText, marginTop: 10 }}>Assessment type: {schedulingData.assessment_type}</p>}
        <Notice title="How to interpret recommendations" tone="orange">Headway suggestions are analytical decision-support outputs based on historical demand indicators and available GTFS schedule patterns. They are not official BMRCL schedules or automatic service changes.</Notice>
      </section>

      <footer style={{ borderTop: `1px solid ${C.border}`, marginTop: 30, paddingTop: 16, color: C.muted, fontSize: 11, lineHeight: 1.8, display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
        <span>AI MetroFlow · Predictive Intelligence</span><span>Model estimates · Historical-data-based decision support</span>
      </footer>
    </main>
  );
}
