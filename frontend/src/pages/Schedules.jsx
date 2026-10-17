
import { useEffect, useState } from "react";
import {
  getMetroRoutes,
  getRouteStations,
  getRouteTrips,
  getRouteFrequency,
  getFrequencyProposals,
  createFrequencyProposal,
  updateFrequencyProposal,
  getDelayRecords,
  createDelayRecord,
  getFrequencyAnalysis,
} from "../services/api";

const LINES = [
  { id: "GREEN", name: "Green Line", color: "#22c55e" },
  { id: "PURPLE", name: "Purple Line", color: "#a78bfa" },
  { id: "YELLOW", name: "Yellow Line", color: "#facc15" },
];

const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  padding: "11px 12px",
  borderRadius: 8,
  border: "1px solid #34445c",
  background: "#08111f",
  color: "#e5edf8",
  outline: "none",
};

const buttonStyle = {
  padding: "10px 15px",
  borderRadius: 8,
  border: "1px solid #34445c",
  background: "#24364d",
  color: "#e5edf8",
  cursor: "pointer",
  fontWeight: 600,
};

function getCollection(data, key) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.[key])) return data[key];
  if (Array.isArray(data?.data)) return data.data;
  return [];
}

function getStationName(station) {
  if (typeof station === "string") return station.trim();
  if (!station || typeof station !== "object") return "";

  return String(
    station.station_name ||
      station.station ||
      station.stop_name ||
      station.name ||
      ""
  ).trim();
}

function formatDate(value) {
  if (!value) return "—";
  return String(value).replace("T", " ").slice(0, 19);
}

function formatNumber(value, digits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";

  return number.toLocaleString(undefined, {
    maximumFractionDigits: digits,
  });
}

function Schedules() {
  const [selectedLine, setSelectedLine] = useState("GREEN");
  const [routes, setRoutes] = useState([]);
  const [stations, setStations] = useState([]);
  const [trips, setTrips] = useState([]);
  const [frequency, setFrequency] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [legacyProposals, setLegacyProposals] = useState([]);
  const [delays, setDelays] = useState([]);

  const [loading, setLoading] = useState(true);
  const [recordsLoading, setRecordsLoading] = useState(true);
  const [error, setError] = useState("");
  const [recordsError, setRecordsError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [saving, setSaving] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const [frequencyAnalysis, setFrequencyAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");
  const [forecastStation, setForecastStation] = useState("");
  const [targetDate, setTargetDate] = useState("2025-10-01");
  const [targetHour, setTargetHour] = useState("18");

  const [proposalForm, setProposalForm] = useState({
    station: "",
    current_headway_minutes: "10",
    proposed_headway_minutes: "8",
    reason: "",
  });

  const [delayForm, setDelayForm] = useState({
    station: "",
    trip_id: "",
    delay_minutes: "5",
    source: "Manual",
    description: "",
  });

  const line = LINES.find((item) => item.id === selectedLine) || LINES[0];

  const cardStyle = {
    background: "#111c2e",
    border: "1px solid #27364b",
    borderRadius: 12,
    padding: 20,
    minWidth: 0,
  };

  const tableStyle = {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: 13,
  };

  const cellStyle = {
    padding: "12px 10px",
    textAlign: "left",
    borderBottom: "1px solid #27364b",
    verticalAlign: "top",
    overflowWrap: "anywhere",
  };

  const gridStyle = {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: 14,
  };

  const labelStyle = {
    display: "block",
    marginBottom: 7,
    color: "#b7c7dc",
    fontSize: 13,
  };

  const routeStationNames = new Set(
    stations
      .map(getStationName)
      .filter(Boolean)
      .map((name) => name.toLowerCase())
  );

  // Load route overview.
  useEffect(() => {
    let cancelled = false;

    async function loadRoutes() {
      try {
        const data = await getMetroRoutes();
        if (!cancelled) setRoutes(getCollection(data, "routes"));
      } catch {
        if (!cancelled) setRoutes([]);
      }
    }

    loadRoutes();
    return () => {
      cancelled = true;
    };
  }, []);

  // Load the selected line's GTFS information.
  useEffect(() => {
    let cancelled = false;

    async function loadLine() {
      setLoading(true);
      setError("");
      setStations([]);
      setTrips([]);
      setFrequency([]);

      try {
        const [stationData, tripData, frequencyData] = await Promise.all([
          getRouteStations(selectedLine),
          getRouteTrips(selectedLine),
          getRouteFrequency(selectedLine),
        ]);

        if (cancelled) return;

        setStations(getCollection(stationData, "stations"));
        setTrips(getCollection(tripData, "trips"));
        setFrequency(getCollection(frequencyData, "frequency"));
      } catch (err) {
        if (!cancelled) {
          setError(
            err.response?.data?.detail ||
              "Could not load this line's schedule. Check the backend and route ID."
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadLine();

    return () => {
      cancelled = true;
    };
  }, [selectedLine, refreshKey]);

  // Load saved proposals and delay records.
  useEffect(() => {
    let cancelled = false;

    async function loadSavedRecords() {
      setRecordsLoading(true);
      setRecordsError("");
      setProposals([]);
      setLegacyProposals([]);
      setDelays([]);

      try {
        const [proposalData, delayData, stationData] = await Promise.all([
          getFrequencyProposals(),
          getDelayRecords(selectedLine),
          getRouteStations(selectedLine),
        ]);

        if (cancelled) return;

        const allProposals = getCollection(proposalData, "proposals");
        const allDelays = getCollection(delayData, "delays");
        const currentStations = getCollection(stationData, "stations");

        const validStationNames = new Set(
          currentStations
            .map(getStationName)
            .filter(Boolean)
            .map((name) => name.toLowerCase())
        );

        const lineProposals = allProposals.filter(
          (item) => item.route_id === selectedLine
        );

        const validProposals = lineProposals.filter((item) => {
          if (!item.station) return true;
          return validStationNames.has(
            String(item.station).trim().toLowerCase()
          );
        });

        const invalidProposals = lineProposals.filter(
          (item) => !validProposals.some((valid) => valid.id === item.id)
        );

        setProposals(validProposals);
        setLegacyProposals(invalidProposals);
        setDelays(allDelays);
      } catch (err) {
        if (!cancelled) {
          setRecordsError(
            err.response?.data?.detail ||
              "Could not load saved scheduling records. Check your login and backend."
          );
        }
      } finally {
        if (!cancelled) setRecordsLoading(false);
      }
    }

    loadSavedRecords();

    return () => {
      cancelled = true;
    };
  }, [selectedLine, refreshKey]);

  // Run the existing ML forecast and scheduling analysis.
  useEffect(() => {
    const station =
      forecastStation ||
      proposalForm.station ||
      getStationName(stations[0]);

    const current = Number(proposalForm.current_headway_minutes);
    const proposed = Number(proposalForm.proposed_headway_minutes);
    const hour = Number(targetHour);

    if (
      !station ||
      !targetDate ||
      !Number.isFinite(hour) ||
      hour < 0 ||
      hour > 23 ||
      !Number.isFinite(current) ||
      !Number.isFinite(proposed) ||
      current <= 0 ||
      proposed <= 0 ||
      current > 240 ||
      proposed > 240
    ) {
      setFrequencyAnalysis(null);
      setAnalysisError("");
      setAnalysisLoading(false);
      return;
    }

    let cancelled = false;

    async function loadFrequencyAnalysis() {
      setAnalysisLoading(true);
      setAnalysisError("");

      try {
        const result = await getFrequencyAnalysis({
          station,
          targetDate,
          targetHour: hour,
          currentHeadway: current,
          proposedHeadway: proposed,
        });

        if (!cancelled) setFrequencyAnalysis(result);
      } catch (err) {
        if (!cancelled) {
          setFrequencyAnalysis(null);
          setAnalysisError(
            err.response?.data?.detail ||
              "Could not load the AI forecast. Check the selected station, forecast date, and backend."
          );
        }
      } finally {
        if (!cancelled) setAnalysisLoading(false);
      }
    }

    loadFrequencyAnalysis();

    return () => {
      cancelled = true;
    };
  }, [
    stations,
    forecastStation,
    proposalForm.station,
    targetDate,
    targetHour,
    proposalForm.current_headway_minutes,
    proposalForm.proposed_headway_minutes,
  ]);

  // Read the exact field names returned by the backend.
  const schedulingRecommendation =
    frequencyAnalysis?.scheduling_recommendation;

  const recommendedHeadway =
    schedulingRecommendation?.recommended_peak_headway_minutes ?? null;

  const schedulingPriority =
    schedulingRecommendation?.priority_level ?? "Not provided";

  const schedulingPriorityScore =
    schedulingRecommendation?.scheduling_priority_score ?? null;

  const schedulingAction =
    schedulingRecommendation?.action ?? "No action provided";

  function renderTable(data, emptyMessage, preferredColumns = null) {
    if (!data.length) {
      return <p style={{ color: "#9caec5" }}>{emptyMessage}</p>;
    }

    const columns =
      preferredColumns || Object.keys(data[0] || {}).slice(0, 6);

    return (
      <div style={{ overflowX: "auto", maxWidth: "100%" }}>
        <table style={tableStyle}>
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  style={{
                    ...cellStyle,
                    color: "#9caec5",
                    fontWeight: 600,
                    whiteSpace: "nowrap",
                  }}
                >
                  {column.replaceAll("_", " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => (
              <tr key={item.id ?? item.trip_id ?? item.stop_id ?? index}>
                {columns.map((column) => (
                  <td key={column} style={cellStyle}>
                    {String(item?.[column] ?? "—")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  async function handleCreateProposal(event) {
    event.preventDefault();
    setSaving(true);
    setActionError("");
    setActionMessage("");

    if (
      proposalForm.station &&
      !routeStationNames.has(proposalForm.station.trim().toLowerCase())
    ) {
      setActionError(
        "Please select a station belonging to the currently selected line."
      );
      setSaving(false);
      return;
    }

    const currentHeadway = Number(proposalForm.current_headway_minutes);
    const proposedHeadway = Number(proposalForm.proposed_headway_minutes);

    if (
      !Number.isFinite(currentHeadway) ||
      !Number.isFinite(proposedHeadway) ||
      currentHeadway <= 0 ||
      proposedHeadway <= 0 ||
      currentHeadway > 240 ||
      proposedHeadway > 240
    ) {
      setActionError(
        "Headway values must be greater than zero and no more than 240 minutes."
      );
      setSaving(false);
      return;
    }

    try {
      await createFrequencyProposal({
        route_id: selectedLine,
        station: proposalForm.station.trim() || null,
        current_headway_minutes: currentHeadway,
        proposed_headway_minutes: proposedHeadway,
        reason: proposalForm.reason.trim(),
      });

      setActionMessage("Frequency proposal saved successfully.");

      setProposalForm((previous) => ({
        ...previous,
        reason: "",
      }));

      setRefreshKey((previous) => previous + 1);
    } catch (err) {
      setActionError(
        err.response?.data?.detail ||
          "Could not save the proposal. Check your login and entered values."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleProposalStatus(proposalId, status) {
    setSaving(true);
    setActionError("");
    setActionMessage("");

    try {
      await updateFrequencyProposal(proposalId, status);
      setActionMessage(`Proposal status updated to ${status}.`);
      setRefreshKey((previous) => previous + 1);
    } catch (err) {
      setActionError(
        err.response?.data?.detail ||
          "Could not update the proposal status."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateDelay(event) {
    event.preventDefault();
    setSaving(true);
    setActionError("");
    setActionMessage("");

    if (
      delayForm.station &&
      !routeStationNames.has(delayForm.station.trim().toLowerCase())
    ) {
      setActionError(
        "Please select a station belonging to the currently selected line."
      );
      setSaving(false);
      return;
    }

    const delayMinutes = Number(delayForm.delay_minutes);

    if (
      !Number.isFinite(delayMinutes) ||
      delayMinutes < 0 ||
      delayMinutes > 1440
    ) {
      setActionError("Delay must be between 0 and 1440 minutes.");
      setSaving(false);
      return;
    }

    try {
      await createDelayRecord({
        route_id: selectedLine,
        station: delayForm.station.trim() || null,
        trip_id: delayForm.trip_id.trim() || null,
        delay_minutes: delayMinutes,
        source: delayForm.source,
        description: delayForm.description.trim() || null,
      });

      setActionMessage("Delay record saved successfully.");

      setDelayForm({
        station: "",
        trip_id: "",
        delay_minutes: "5",
        source: "Manual",
        description: "",
      });

      setRefreshKey((previous) => previous + 1);
    } catch (err) {
      setActionError(
        err.response?.data?.detail ||
          "Could not save the delay record. Check your login and entered values."
      );
    } finally {
      setSaving(false);
    }
  }

  function renderStationOptions() {
    return stations.map((station, index) => {
      const name = getStationName(station);

      return name ? (
        <option key={`${name}-${index}`} value={name}>
          {name}
        </option>
      ) : null;
    });
  }

  return (
    <div
      style={{
        minHeight: "100%",
        padding: 28,
        background: "#08111f",
        color: "#e5edf8",
      }}
    >
      <div style={{ marginBottom: 24 }}>
        <div
          style={{
            color: "#60a5fa",
            fontSize: 12,
            letterSpacing: 2,
          }}
        >
          AI METROFLOW / OPERATIONS
        </div>

        <h1 style={{ marginBottom: 8 }}>Schedules &amp; Frequency</h1>

        <p style={{ color: "#9caec5", lineHeight: 1.6 }}>
          Explore GTFS schedule information, use model-based ridership
          forecasts to inform frequency proposals, and maintain delay records.
        </p>
      </div>

      <div
        style={{
          ...cardStyle,
          marginBottom: 20,
          borderLeft: `4px solid ${line.color}`,
        }}
      >
        <div style={{ marginBottom: 12, fontSize: 13, color: "#9caec5" }}>
          SELECT METRO LINE
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {LINES.map((item) => (
            <button
              type="button"
              key={item.id}
              onClick={() => {
                setSelectedLine(item.id);
                setActionMessage("");
                setActionError("");
                setForecastStation("");

                setProposalForm((previous) => ({
                  ...previous,
                  station: "",
                }));

                setDelayForm((previous) => ({
                  ...previous,
                  station: "",
                  trip_id: "",
                }));
              }}
              style={{
                ...buttonStyle,
                border:
                  selectedLine === item.id
                    ? `2px solid ${item.color}`
                    : "1px solid #34445c",
                background:
                  selectedLine === item.id ? "#26364b" : "#111c2e",
              }}
            >
              {item.name}
            </button>
          ))}
        </div>

        <p style={{ marginBottom: 0, color: "#9caec5", fontSize: 12 }}>
          {routes.length
            ? `${routes.length} route record(s) returned by the backend`
            : "Route summary will be shown when available."}
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
          gap: 16,
          marginBottom: 20,
        }}
      >
        <div style={cardStyle}>
          <p style={{ color: "#9caec5", marginTop: 0 }}>Selected Line</p>
          <h2 style={{ color: line.color }}>{line.name}</h2>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#9caec5", marginTop: 0 }}>Stations</p>
          <h2>{loading ? "…" : stations.length}</h2>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#9caec5", marginTop: 0 }}>Scheduled Trips</p>
          <h2>{loading ? "…" : trips.length}</h2>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#9caec5", marginTop: 0 }}>
            Frequency Records
          </p>
          <h2>{loading ? "…" : frequency.length}</h2>
        </div>
      </div>

      <div
        style={{
          background: "#17263a",
          border: "1px solid #35465e",
          borderRadius: 10,
          padding: 14,
          marginBottom: 20,
          fontSize: 13,
          lineHeight: 1.6,
        }}
      >
        <strong>Data status:</strong> GTFS records describe scheduled service.
        Forecasts are model-generated, not live passenger counts. Frequency
        recommendations are analytical and do not change official metro
        operations.
      </div>

      {loading ? (
        <div style={cardStyle}>Loading {line.name} schedule data…</div>
      ) : error ? (
        <div style={{ ...cardStyle, borderColor: "#ef4444" }}>
          <h3>Unable to load schedule</h3>
          <p>{error}</p>
          <button
            type="button"
            style={buttonStyle}
            onClick={() => setRefreshKey((previous) => previous + 1)}
          >
            Retry
          </button>
        </div>
      ) : (
        <div style={{ display: "grid", gap: 20 }}>
          <section style={cardStyle}>
            <h2>Station List</h2>
            {renderTable(stations, "No station records returned for this line.")}
          </section>

          <section style={cardStyle}>
            <h2>Scheduled Trips</h2>
            {renderTable(trips, "No trip records returned for this line.")}
          </section>

          <section style={cardStyle}>
            <h2>Service Frequency</h2>
            {renderTable(
              frequency,
              "No frequency records returned for this line."
            )}
          </section>
        </div>
      )}

      <div style={{ display: "grid", gap: 20, marginTop: 24 }}>
        <section style={cardStyle}>
          <h2>AI Frequency Optimization</h2>

          <p style={{ color: "#9caec5", lineHeight: 1.6 }}>
            Select a station and forecast period. The analysis combines the
            backend ridership forecast with its existing analytical scheduling
            recommendation. You can then save a frequency proposal.
          </p>

          <form onSubmit={handleCreateProposal} style={gridStyle}>
            <div>
              <label style={labelStyle}>Proposal station (optional)</label>
              <select
                value={proposalForm.station}
                onChange={(event) =>
                  setProposalForm((previous) => ({
                    ...previous,
                    station: event.target.value,
                  }))
                }
                style={inputStyle}
              >
                <option value="">All stations / route level</option>
                {renderStationOptions()}
              </select>
            </div>

            <div>
              <label style={labelStyle}>Current headway (minutes)</label>
              <input
                type="number"
                min="0.1"
                max="240"
                step="any"
                required
                value={proposalForm.current_headway_minutes}
                onChange={(event) =>
                  setProposalForm((previous) => ({
                    ...previous,
                    current_headway_minutes: event.target.value,
                  }))
                }
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Proposed headway (minutes)</label>
              <input
                type="number"
                min="0.1"
                max="240"
                step="any"
                required
                value={proposalForm.proposed_headway_minutes}
                onChange={(event) =>
                  setProposalForm((previous) => ({
                    ...previous,
                    proposed_headway_minutes: event.target.value,
                  }))
                }
                style={inputStyle}
              />
            </div>

            {/* ML forecast and analytical scheduling recommendation */}
            <div
              style={{
                gridColumn: "1 / -1",
                padding: 18,
                border: "1px solid #36516f",
                borderRadius: 10,
                background: "#0c1728",
              }}
            >
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 10,
                }}
              >
                <h3 style={{ margin: 0 }}>
                  AI Ridership Forecast &amp; Frequency Optimization
                </h3>

                <span
                  style={{
                    fontSize: 11,
                    padding: "5px 8px",
                    borderRadius: 20,
                    background: "#123c2b",
                    color: "#86efac",
                    border: "1px solid #166534",
                  }}
                >
                  ML-POWERED ANALYSIS
                </span>
              </div>

              <p style={{ color: "#9caec5", lineHeight: 1.6 }}>
                Forecast passenger demand using the existing trained ridership
                model and retrieve the backend scheduling recommendation.
              </p>

              <div style={gridStyle}>
                <div>
                  <label style={labelStyle}>Forecast station</label>
                  <select
                    value={
                      forecastStation ||
                      proposalForm.station ||
                      getStationName(stations[0])
                    }
                    onChange={(event) =>
                      setForecastStation(event.target.value)
                    }
                    style={inputStyle}
                    required
                  >
                    {renderStationOptions()}
                  </select>
                </div>

                <div>
                  <label style={labelStyle}>Forecast date</label>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={(event) => setTargetDate(event.target.value)}
                    required
                    style={inputStyle}
                  />
                </div>

                <div>
                  <label style={labelStyle}>Forecast hour (0–23)</label>
                  <select
                    value={targetHour}
                    onChange={(event) => setTargetHour(event.target.value)}
                    style={inputStyle}
                  >
                    {Array.from({ length: 24 }, (_, hour) => (
                      <option key={hour} value={String(hour)}>
                        {String(hour).padStart(2, "0")}:00
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {analysisLoading ? (
                <p style={{ color: "#93c5fd", marginTop: 18 }}>
                  Running the ridership forecast and scheduling analysis…
                </p>
              ) : analysisError ? (
                <div
                  role="alert"
                  style={{
                    marginTop: 18,
                    padding: 12,
                    borderRadius: 8,
                    border: "1px solid #7f1d1d",
                    background: "#2b1118",
                    color: "#fca5a5",
                    lineHeight: 1.6,
                  }}
                >
                  {analysisError}
                  <p style={{ marginBottom: 0, fontSize: 12 }}>
                    Some stations may not have a scheduling recommendation.
                    Try a station supported by the backend scheduling
                    intelligence.
                  </p>
                </div>
              ) : frequencyAnalysis ? (
                <>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "repeat(auto-fit, minmax(175px, 1fr))",
                      gap: 12,
                      marginTop: 20,
                    }}
                  >
                    <div
                      style={{
                        padding: 16,
                        border: "1px solid #36516f",
                        borderRadius: 9,
                        background: "#111c2e",
                      }}
                    >
                      <p style={{ color: "#9caec5", fontSize: 12 }}>
                        Predicted passenger demand
                      </p>
                      <h2 style={{ color: "#60a5fa", margin: "8px 0" }}>
                        {formatNumber(frequencyAnalysis.predicted_ridership)}
                      </h2>
                      <p style={{ color: "#8195af", fontSize: 12 }}>
                        {frequencyAnalysis.unit || "Passengers"} ·{" "}
                        {frequencyAnalysis.target_datetime}
                      </p>
                    </div>

                    <div
                      style={{
                        padding: 16,
                        border: "1px solid #36516f",
                        borderRadius: 9,
                        background: "#111c2e",
                      }}
                    >
                      <p style={{ color: "#9caec5", fontSize: 12 }}>
                        AI-recommended headway
                      </p>
                      <h2 style={{ color: "#86efac", margin: "8px 0" }}>
                        {recommendedHeadway != null
                          ? `${formatNumber(recommendedHeadway)} min`
                          : "Not provided"}
                      </h2>
                      <p style={{ color: "#8195af", fontSize: 12 }}>
                        Analytical recommendation, not an official timetable
                      </p>
                    </div>

                    <div
                      style={{
                        padding: 16,
                        border: "1px solid #36516f",
                        borderRadius: 9,
                        background: "#111c2e",
                      }}
                    >
                      <p style={{ color: "#9caec5", fontSize: 12 }}>
                        Scheduling priority
                      </p>
                      <h2 style={{ color: "#facc15", margin: "8px 0" }}>
                        {schedulingPriority}
                      </h2>
                      <p style={{ color: "#8195af", fontSize: 12 }}>
                        Existing scheduling intelligence
                      </p>
                    </div>

                    <div
                      style={{
                        padding: 16,
                        border: "1px solid #36516f",
                        borderRadius: 9,
                        background: "#111c2e",
                      }}
                    >
                      <p style={{ color: "#9caec5", fontSize: 12 }}>
                        Scheduling priority score
                      </p>
                      <h2 style={{ color: "#c4b5fd", margin: "8px 0" }}>
                        {schedulingPriorityScore != null
                          ? formatNumber(schedulingPriorityScore, 3)
                          : "Not provided"}
                      </h2>
                      <p style={{ color: "#8195af", fontSize: 12 }}>
                        Analytical score, not a probability
                      </p>
                    </div>
                  </div>

                  <div
                    style={{
                      marginTop: 16,
                      padding: 14,
                      borderRadius: 8,
                      background: "#14263a",
                      border: "1px solid #29435f",
                      lineHeight: 1.7,
                    }}
                  >
                    <strong>Scheduling insight</strong>
                    <p style={{ margin: "8px 0" }}>{schedulingAction}</p>
                    {schedulingRecommendation?.peak_demand_per_headway !=
                      null && (
                      <p style={{ margin: "6px 0" }}>
                        Peak demand per headway:{" "}
                        {formatNumber(
                          schedulingRecommendation.peak_demand_per_headway
                        )}
                      </p>
                    )}
                    {schedulingRecommendation?.service_gap_ratio != null && (
                      <p style={{ margin: "6px 0" }}>
                        Service gap ratio:{" "}
                        {formatNumber(
                          schedulingRecommendation.service_gap_ratio
                        )}
                      </p>
                    )}
                    {schedulingRecommendation?.demand_concentration != null && (
                      <p style={{ margin: "6px 0" }}>
                        Demand concentration:{" "}
                        {formatNumber(
                          schedulingRecommendation.demand_concentration
                        )}
                      </p>
                    )}
                  </div>

                  <div
                    style={{
                      marginTop: 16,
                      padding: 14,
                      borderRadius: 8,
                      background: "#14263a",
                      border: "1px solid #29435f",
                      lineHeight: 1.7,
                    }}
                  >
                    <strong>Forecast details</strong>
                    <p style={{ marginBottom: 6 }}>
                      Station: {frequencyAnalysis.station}
                    </p>
                    <p style={{ margin: "6px 0" }}>
                      Model:{" "}
                      {frequencyAnalysis.model || "Existing prediction model"}
                    </p>
                    <p style={{ margin: "6px 0" }}>
                      Forecast type:{" "}
                      {frequencyAnalysis.forecast_type || "Model forecast"}
                    </p>
                    <p style={{ margin: "6px 0" }}>
                      Data mode:{" "}
                      {frequencyAnalysis.data_mode || "Dataset-based"}
                    </p>
                    <p style={{ margin: "6px 0" }}>
                      Forecast steps: {frequencyAnalysis.forecast_steps ?? "—"}
                    </p>
                    {frequencyAnalysis.forecast_note && (
                      <p style={{ color: "#bfdbfe", marginBottom: 0 }}>
                        {frequencyAnalysis.forecast_note}
                      </p>
                    )}
                  </div>

                  <div
                    style={{
                      marginTop: 12,
                      padding: 14,
                      border: "1px solid #34445c",
                      borderRadius: 8,
                      lineHeight: 1.7,
                    }}
                  >
                    <strong>Frequency comparison</strong>
                    <p style={{ marginBottom: 6 }}>
                      Current: {frequencyAnalysis.current_headway_minutes} min
                      {" · "}
                      {frequencyAnalysis.current_services_per_hour}{" "}
                      services/hour
                    </p>
                    <p style={{ margin: "6px 0" }}>
                      Proposed: {frequencyAnalysis.proposed_headway_minutes}{" "}
                      min
                      {" · "}
                      {frequencyAnalysis.proposed_services_per_hour}{" "}
                      services/hour
                    </p>
                    <p style={{ marginBottom: 0 }}>
                      Mathematical frequency change:{" "}
                      {Number(frequencyAnalysis.frequency_change_percent) > 0
                        ? "+"
                        : ""}
                      {formatNumber(
                        frequencyAnalysis.frequency_change_percent
                      )}
                      %
                    </p>
                  </div>

                  <p
                    style={{
                      color: "#fbbf24",
                      fontSize: 12,
                      lineHeight: 1.7,
                      marginBottom: 0,
                      marginTop: 14,
                    }}
                  >
                    The model forecasts ridership; the separate scheduling
                    intelligence provides the headway recommendation. This
                    analysis does not prove that a proposed headway will reduce
                    crowding or waiting time, and it does not change actual
                    metro operations.
                  </p>
                </>
              ) : (
                <p style={{ color: "#9caec5", marginTop: 18 }}>
                  Select a station and forecast period to load the AI analysis.
                </p>
              )}
            </div>

            <div style={{ gridColumn: "1 / -1" }}>
              <label style={labelStyle}>Reason for the proposal</label>
              <textarea
                required
                minLength={3}
                maxLength={2000}
                value={proposalForm.reason}
                onChange={(event) =>
                  setProposalForm((previous) => ({
                    ...previous,
                    reason: event.target.value,
                  }))
                }
                placeholder="Explain the demand pattern or analytical reason..."
                rows={3}
                style={{ ...inputStyle, resize: "vertical" }}
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={saving || loading || Boolean(error)}
                style={{
                  ...buttonStyle,
                  background: "#14532d",
                  borderColor: "#22c55e",
                  opacity: saving || loading || error ? 0.65 : 1,
                }}
              >
                {saving ? "Saving…" : "Save Frequency Proposal"}
              </button>
            </div>
          </form>

          <div style={{ marginTop: 24 }}>
            <h3>Saved Proposals — {line.name}</h3>

            {recordsLoading ? (
              <p style={{ color: "#9caec5" }}>Loading saved records…</p>
            ) : recordsError ? (
              <p style={{ color: "#fca5a5" }}>{recordsError}</p>
            ) : proposals.length === 0 ? (
              <p style={{ color: "#9caec5" }}>
                No valid saved proposals for this line yet.
              </p>
            ) : (
              <div style={{ display: "grid", gap: 12 }}>
                {proposals.map((proposal) => (
                  <div
                    key={proposal.id}
                    style={{
                      padding: 15,
                      border: "1px solid #34445c",
                      borderRadius: 10,
                      background: "#0c1728",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: 10,
                        justifyContent: "space-between",
                      }}
                    >
                      <strong>
                        {proposal.station || "Route-wide proposal"}
                      </strong>
                      <span style={{ color: "#facc15" }}>
                        {proposal.status}
                      </span>
                    </div>

                    <p style={{ lineHeight: 1.6 }}>
                      Headway: {proposal.current_headway_minutes} min
                      {" → "}
                      {proposal.proposed_headway_minutes} min
                    </p>

                    <p style={{ color: "#b7c7dc", lineHeight: 1.6 }}>
                      {proposal.reason}
                    </p>

                    <p style={{ color: "#8195af", fontSize: 12 }}>
                      Proposal ID: {proposal.id}
                      {proposal.created_at
                        ? ` · Created: ${formatDate(proposal.created_at)}`
                        : ""}
                    </p>

                    {proposal.status === "Proposed" && (
                      <div
                        style={{
                          display: "flex",
                          flexWrap: "wrap",
                          gap: 8,
                        }}
                      >
                        <button
                          type="button"
                          disabled={saving}
                          style={buttonStyle}
                          onClick={() =>
                            handleProposalStatus(proposal.id, "Approved")
                          }
                        >
                          Approve
                        </button>

                        <button
                          type="button"
                          disabled={saving}
                          style={buttonStyle}
                          onClick={() =>
                            handleProposalStatus(proposal.id, "Rejected")
                          }
                        >
                          Reject
                        </button>
                      </div>
                    )}

                    {proposal.status === "Approved" && (
                      <button
                        type="button"
                        disabled={saving}
                        style={buttonStyle}
                        onClick={() =>
                          handleProposalStatus(proposal.id, "Completed")
                        }
                      >
                        Mark Completed
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {!recordsLoading &&
              !recordsError &&
              legacyProposals.length > 0 && (
                <div
                  style={{
                    marginTop: 16,
                    padding: 15,
                    border: "1px solid #a16207",
                    background: "#2b2114",
                    borderRadius: 10,
                  }}
                >
                  <h4 style={{ marginTop: 0, color: "#fbbf24" }}>
                    Legacy proposals excluded from the active list
                  </h4>

                  <p style={{ color: "#e5c98a", lineHeight: 1.6 }}>
                    {legacyProposals.length} saved proposal(s) refer to a
                    station not found in the selected line's station list.
                    These records have not been deleted or changed.
                  </p>

                  {legacyProposals.map((proposal) => (
                    <div
                      key={proposal.id}
                      style={{
                        padding: 10,
                        borderTop: "1px solid #6b4b1f",
                      }}
                    >
                      <strong>
                        {proposal.station || "Route-wide proposal"}
                      </strong>
                      <p style={{ marginBottom: 4 }}>
                        Proposal ID: {proposal.id} · Route: {proposal.route_id}
                      </p>
                      <p style={{ marginTop: 4, color: "#e5c98a" }}>
                        {proposal.current_headway_minutes} →{" "}
                        {proposal.proposed_headway_minutes} minutes ·{" "}
                        {proposal.status}
                      </p>
                    </div>
                  ))}
                </div>
              )}
          </div>
        </section>

        <section style={cardStyle}>
          <h2>Delay Record Management</h2>

          <p style={{ color: "#9caec5", lineHeight: 1.6 }}>
            Save a delay record for {line.name}. Choose Demo when testing sample
            data; choose Manual for a manually entered record. Neither source
            automatically verifies a real train delay.
          </p>

          <form onSubmit={handleCreateDelay} style={gridStyle}>
            <div>
              <label style={labelStyle}>Station (optional)</label>
              <select
                value={delayForm.station}
                onChange={(event) =>
                  setDelayForm((previous) => ({
                    ...previous,
                    station: event.target.value,
                  }))
                }
                style={inputStyle}
              >
                <option value="">No station selected</option>
                {renderStationOptions()}
              </select>
            </div>

            <div>
              <label style={labelStyle}>Trip ID (optional)</label>
              <input
                value={delayForm.trip_id}
                onChange={(event) =>
                  setDelayForm((previous) => ({
                    ...previous,
                    trip_id: event.target.value,
                  }))
                }
                placeholder="Enter a trip ID if known"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Delay (minutes)</label>
              <input
                type="number"
                min="0"
                max="1440"
                step="any"
                required
                value={delayForm.delay_minutes}
                onChange={(event) =>
                  setDelayForm((previous) => ({
                    ...previous,
                    delay_minutes: event.target.value,
                  }))
                }
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Record source</label>
              <select
                value={delayForm.source}
                onChange={(event) =>
                  setDelayForm((previous) => ({
                    ...previous,
                    source: event.target.value,
                  }))
                }
                style={inputStyle}
              >
                <option value="Manual">Manual</option>
                <option value="Demo">Demo</option>
              </select>
            </div>

            <div style={{ gridColumn: "1 / -1" }}>
              <label style={labelStyle}>Description (optional)</label>
              <textarea
                maxLength={2000}
                value={delayForm.description}
                onChange={(event) =>
                  setDelayForm((previous) => ({
                    ...previous,
                    description: event.target.value,
                  }))
                }
                placeholder="Add context about this manually entered or demo record..."
                rows={3}
                style={{ ...inputStyle, resize: "vertical" }}
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={saving || loading || Boolean(error)}
                style={{
                  ...buttonStyle,
                  background: "#78350f",
                  borderColor: "#f59e0b",
                  opacity: saving || loading || error ? 0.65 : 1,
                }}
              >
                {saving ? "Saving…" : "Save Delay Record"}
              </button>
            </div>
          </form>

          <div style={{ marginTop: 24 }}>
            <h3>Saved Delay Records — {line.name}</h3>

            {recordsLoading ? (
              <p style={{ color: "#9caec5" }}>Loading saved records…</p>
            ) : recordsError ? (
              <p style={{ color: "#fca5a5" }}>{recordsError}</p>
            ) : delays.length === 0 ? (
              <p style={{ color: "#9caec5" }}>
                No delay records saved for this line yet.
              </p>
            ) : (
              <div style={{ overflowX: "auto", maxWidth: "100%" }}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      {[
                        "Station",
                        "Trip ID",
                        "Delay (minutes)",
                        "Source",
                        "Description",
                        "Recorded at",
                      ].map((column) => (
                        <th
                          key={column}
                          style={{
                            ...cellStyle,
                            color: "#9caec5",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {delays.map((record) => (
                      <tr key={record.id}>
                        <td style={cellStyle}>{record.station || "—"}</td>
                        <td style={cellStyle}>{record.trip_id || "—"}</td>
                        <td style={cellStyle}>{record.delay_minutes}</td>
                        <td style={cellStyle}>{record.source || "—"}</td>
                        <td style={cellStyle}>
                          {record.description || "—"}
                        </td>
                        <td style={cellStyle}>
                          {formatDate(record.recorded_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        {(actionMessage || actionError) && (
          <div
            role="status"
            style={{
              ...cardStyle,
              borderColor: actionError ? "#ef4444" : "#22c55e",
              color: actionError ? "#fca5a5" : "#86efac",
            }}
          >
            {actionError || actionMessage}
          </div>
        )}

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            type="button"
            style={buttonStyle}
            disabled={saving || recordsLoading}
            onClick={() => {
              setActionMessage("");
              setActionError("");
              setRefreshKey((previous) => previous + 1);
            }}
          >
            Refresh Scheduling Data
          </button>
        </div>
      </div>
    </div>
  );
}

export default Schedules;
