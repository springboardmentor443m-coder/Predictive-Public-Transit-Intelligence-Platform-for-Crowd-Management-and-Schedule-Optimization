
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Activity,
  RefreshCw,
  Users,
  MapPin,
  TrendingUp,
  ArrowRightLeft,
  AlertTriangle,
  Grid3X3,
  Download,
} from "lucide-react";

import "../styles/StationIntelligence.css";

import {
  getCrowdStatus,
  getCrowdHotspots,
  getCrowdFlow,
  getCrowdHeatmap,
  getCrowdDemandPressure,
  getDemoLiveMonitoring,
  getNetworkOperations,
  getLatestStationPrediction,
  getStationHourlyForecast,
} from "../services/api";

const formatNumber = (value) => {
  if (value === null || value === undefined || value === "") return "—";

  const number = Number(value);

  return Number.isFinite(number)
    ? number.toLocaleString("en-IN", { maximumFractionDigits: 2 })
    : "—";
};

const formatHour = (value) => {
  const hour = Number(value);

  return Number.isInteger(hour) && hour >= 0 && hour <= 23
    ? `${String(hour).padStart(2, "0")}:00`
    : "—";
};

const titleCase = (value) =>
  String(value || "Unknown")
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase());

const demandClass = (value) => {
  const status = String(value || "").toLowerCase();

  if (status === "high" || status === "critical") return "high";
  if (status === "moderate" || status === "medium") return "moderate";
  if (status === "low") return "low";

  return "unknown";
};

const finite = (value) =>
  value === null ||
  value === undefined ||
  value === "" ||
  !Number.isFinite(Number(value))
    ? null
    : Number(value);

const stationName = (row) =>
  row?.station ?? row?.Station ?? row?.station_name ?? "Unknown station";

const currentRidership = (row) =>
  row?.current_ridership ??
  row?.current_entries ??
  row?.ridership ??
  row?.Ridership ??
  row?.entries ??
  null;

const entries = (row) =>
  row?.current_entries ??
  row?.entries ??
  row?.Ridership_entry ??
  row?.ridership_entry ??
  null;

const exits = (row) =>
  row?.current_exit ??
  row?.current_exits ??
  row?.exits ??
  row?.Ridership_exit ??
  row?.ridership_exit ??
  null;

const prediction = (row) =>
  row?.predicted_next_hour_ridership ??
  row?.ml_predicted_next_hour_ridership ??
  row?.predicted_ridership ??
  row?.predicted_demand ??
  row?.ai_prediction ??
  row?.predicted ??
  row?.predicted_next_hour ??
  null;

// Reads the real fields returned by GET /prediction/crowd/latest/{station}:
// latest_date + latest_hour = the observation the model used,
// and the target is that observation hour + 1.
const predictionTiming = (row) => {
  const hour = Number(row?.latest_hour);
  const match = String(row?.latest_date ?? "").match(
    /^(\d{4})-(\d{2})-(\d{2})/
  );

  if (!match || row?.latest_hour == null || !Number.isFinite(hour)) {
    return null;
  }

  const [year, month, day] = [match[1], match[2], match[3]].map(Number);
  const target = new Date(Date.UTC(year, month - 1, day, hour + 1));

  return {
    sourceDate: `${match[1]}-${match[2]}-${match[3]}`,
    sourceHour: hour,
    targetDate: target.toISOString().slice(0, 10),
    targetHour: target.getUTCHours(),
  };
};

// Adds (or subtracts) whole days to a YYYY-MM-DD string using UTC maths,
// so the result never shifts with the browser's time zone.
const shiftIsoDate = (isoDate, days) => {
  const match = String(isoDate ?? "").match(/^(\d{4})-(\d{2})-(\d{2})$/);

  if (!match) return "";

  const shifted = new Date(
    Date.UTC(
      Number(match[1]),
      Number(match[2]) - 1,
      Number(match[3]) + days
    )
  );

  return shifted.toISOString().slice(0, 10);
};

const pressure = (row) =>
  row?.pressure_score ??
  row?.demand_pressure ??
  row?.["Demand Pressure"] ??
  null;

const pressureLevel = (row) =>
  row?.congestion_level ??
  row?.pressure_level ??
  row?.demand_level ??
  row?.demand_status ??
  row?.status ??
  row?.["Demand Status"] ??
  "Unavailable";

function MetricCard({
  tone = "blue",
  icon: Icon,
  label,
  value,
  detail,
}) {
  return (
    <article className={`station-metric-card ${tone}`}>
      <div className="station-metric-label">
        {Icon && <Icon size={15} />}
        {label}
      </div>

      <strong className="station-metric-value">{value}</strong>

      {detail && (
        <div className="station-metric-detail">{detail}</div>
      )}
    </article>
  );
}

function CrowdMonitoring() {
  const [statusRows, setStatusRows] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [flows, setFlows] = useState([]);
  const [heatmapRows, setHeatmapRows] = useState([]);
  const [pressureRows, setPressureRows] = useState([]);

  const [liveMonitoring, setLiveMonitoring] = useState(null);
  const [liveError, setLiveError] = useState("");
  const [liveUpdatedAt, setLiveUpdatedAt] = useState(null);

  const [networkOperations, setNetworkOperations] = useState(null);
  const [operationsError, setOperationsError] = useState("");
  const [operationsLoading, setOperationsLoading] = useState(false);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [demandFilter, setDemandFilter] = useState("All");

  const [heatmapSearch, setHeatmapSearch] = useState("");
  const [selectedHeatmapHour, setSelectedHeatmapHour] =
    useState("All");

  const [selectedStation, setSelectedStation] = useState("");
  const [selectedStationHour, setSelectedStationHour] =
    useState("18");

  // Station-specific next-hour AI prediction state.
  const [stationPrediction, setStationPrediction] = useState(null);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionError, setPredictionError] = useState("");

  // Future hourly forecast, rolled forward by the trained model.
  const [forecastDate, setForecastDate] = useState("");
  const [forecastHour, setForecastHour] = useState("9");
  const [forecastResult, setForecastResult] = useState(null);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastError, setForecastError] = useState("");
  const forecastRequestRef = useRef(0);

  const loadCrowdData = useCallback(async (manual = false) => {
    if (manual) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError("");

    try {
      const results = await Promise.allSettled([
        getCrowdStatus(),
        getCrowdHotspots(),
        getCrowdFlow(),
        getCrowdHeatmap(),
        getCrowdDemandPressure(),
      ]);

      const setters = [
        setStatusRows,
        setHotspots,
        setFlows,
        setHeatmapRows,
        setPressureRows,
      ];

      const keys = [
        "crowd_status",
        "hotspots",
        "station_flow",
        "heatmap",
        "demand_pressure",
      ];

      const names = [
        "station demand status",
        "historical hotspots",
        "passenger flow",
        "crowd heatmap",
        "demand-pressure scores",
      ];

      const failed = [];

      results.forEach((result, index) => {
        const rows =
          result.status === "fulfilled"
            ? result.value?.[keys[index]]
            : null;

        if (Array.isArray(rows)) {
          setters[index](rows);
        } else {
          setters[index]([]);
          failed.push(names[index]);
        }
      });

      if (failed.length === results.length) {
        setError(
          "Crowd data could not be loaded. Check the backend connection and login status."
        );
      } else if (failed.length) {
        setError(
          `Unable to load ${failed.join(
            ", "
          )}. Other available data is displayed.`
        );
      }
    } catch {
      setError(
        "Unable to load crowd monitoring data. Check the backend connection and login status."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const loadOperations = useCallback(async () => {
    setOperationsLoading(true);
    setOperationsError("");

    try {
      const data = await getNetworkOperations("2025-09-30", 18);
      setNetworkOperations(data);
    } catch (error) {
      setNetworkOperations(null);
      setOperationsError(
        error?.response?.data?.detail ||
          error?.message ||
          "Unable to load network-wide AI operations."
      );
    } finally {
      setOperationsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCrowdData();
  }, [loadCrowdData]);

  useEffect(() => {
    loadOperations();
  }, [loadOperations]);

  // This section is explicitly simulated, not a verified live BMRCL feed.
  useEffect(() => {
    let mounted = true;
    let busy = false;

    const refresh = async () => {
      if (busy) return;

      busy = true;

      try {
        const data = await getDemoLiveMonitoring();

        if (!mounted) return;

        if (!Array.isArray(data?.station_snapshots)) {
          throw new Error("Invalid simulated-live response");
        }

        setLiveMonitoring(data);
        setLiveUpdatedAt(new Date());
        setLiveError("");
      } catch {
        if (mounted) {
          setLiveError(
            "Simulated-live monitoring is temporarily unavailable. Check the backend connection and login status."
          );
        }
      } finally {
        busy = false;
      }
    };

    refresh();

    const intervalId = window.setInterval(refresh, 5000);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  // Fetch the latest available station prediction whenever the station changes.
  useEffect(() => {
    if (!selectedStation) {
      setStationPrediction(null);
      setPredictionError("");
      setPredictionLoading(false);
      return;
    }

    let active = true;

    // A forecast belongs to one station, so clear it when the station changes.
    forecastRequestRef.current += 1;
    setForecastResult(null);
    setForecastError("");
    setForecastLoading(false);
    setForecastDate("");

    setStationPrediction(null);
    setPredictionError("");
    setPredictionLoading(true);

    getLatestStationPrediction(selectedStation)
      .then((data) => {
        if (!active) return;

        // The backend answers HTTP 200 with a "message" when the station is
        // not found, so a missing prediction value must be shown as an error.
        if (data?.predicted_next_hour_ridership == null) {
          setStationPrediction(null);
          setPredictionError(
            data?.message ||
              "The response did not include a predicted value."
          );
          return;
        }

        setStationPrediction(data);
      })
      .catch((error) => {
        if (active) {
          setStationPrediction(null);
          setPredictionError(
            error?.response?.data?.detail ||
              "No next-hour prediction is available for this station."
          );
        }
      })
      .finally(() => {
        if (active) {
          setPredictionLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedStation]);

  const runForecast = async () => {
    const timing = predictionTiming(stationPrediction);
    const targetDate = forecastDate || timing?.targetDate;

    if (!selectedStation || !targetDate) {
      setForecastError("Choose a station and a target date first.");
      return;
    }

    const requestId = forecastRequestRef.current + 1;
    forecastRequestRef.current = requestId;

    setForecastLoading(true);
    setForecastError("");
    setForecastResult(null);

    try {
      const data = await getStationHourlyForecast(
        selectedStation,
        targetDate,
        forecastHour
      );

      // Ignore the answer if the station changed or a newer request started.
      if (requestId !== forecastRequestRef.current) return;

      if (data?.predicted_ridership == null) {
        setForecastError(
          data?.message ||
            "The forecast response did not include a predicted value."
        );
      } else {
        setForecastResult(data);
      }
    } catch (error) {
      if (requestId !== forecastRequestRef.current) return;

      const detail = error?.response?.data?.detail;

      setForecastError(
        typeof detail === "string"
          ? detail
          : "Unable to generate the forecast. Check the backend connection and login status."
      );
    } finally {
      if (requestId === forecastRequestRef.current) {
        setForecastLoading(false);
      }
    }
  };

  const exportCSV = useCallback(() => {
    const sections = [
      [
        "station-demand",
        ["Station", "Hour", "Total Ridership (all dates)", "Demand Status"],
        statusRows.map((row) => [
          row.Station,
          formatHour(row.Hour),
          row.Ridership,
          row["Demand Status"],
        ]),
      ],
      [
        "heatmap",
        ["Station", "Hour", "Total Ridership (all dates)", "Demand Status"],
        heatmapRows.map((row) => [
          row.Station,
          formatHour(row.Hour),
          row.Ridership,
          row["Demand Status"],
        ]),
      ],
      [
        "demand-pressure",
        [
          "Station",
          "Hour",
          "Demand Pressure",
          "Station Average Ridership",
          "Demand vs Average (%)",
        ],
        pressureRows.map((row) => [
          row.Station,
          formatHour(row.Hour),
          row["Demand Pressure"],
          row["Station Average Ridership"],
          row["Demand vs Average (%)"],
        ]),
      ],
      [
        "historical-hotspots",
        ["Rank", "Station", "Hour", "Total Ridership (all dates)"],
        hotspots.map((row, index) => [
          index + 1,
          row.Station,
          formatHour(row.Hour),
          row.Ridership,
        ]),
      ],
      [
        "historical-passenger-flow",
        ["Station", "Entries", "Exits", "Net Flow"],
        flows.map((row) => [
          row.Station,
          row.Ridership_entry,
          row.Ridership_exit,
          row["Net Flow"],
        ]),
      ],
    ].filter((section) => section[2].length);

    if (!sections.length) {
      window.alert("No historical crowd data is available to export.");
      return;
    }

    sections.forEach(([name, headers, rows]) => {
      const escapeCSV = (value) =>
        `"${String(value ?? "").replace(/"/g, '""')}"`;

      const content = [headers, ...rows]
        .map((row) => row.map(escapeCSV).join(","))
        .join("\r\n");

      const url = URL.createObjectURL(
        new Blob(["\uFEFF", content], {
          type: "text/csv;charset=utf-8;",
        })
      );

      const link = document.createElement("a");
      link.href = url;
      link.download = `metroflow-${name}.csv`;

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    });

    if (sections.length > 1) {
      window.alert(
        `${sections.length} CSV files are being downloaded. Check your Downloads folder.`
      );
    }
  }, [statusRows, heatmapRows, pressureRows, hotspots, flows]);

  const stations = useMemo(() => {
    const stationMap = new Map();

    statusRows.forEach((row) => {
      if (!row.Station) return;

      const existing = stationMap.get(row.Station);

      if (
        !existing ||
        Number(row.Ridership ?? 0) >
          Number(existing.Ridership ?? 0)
      ) {
        stationMap.set(row.Station, row);
      }
    });

    return [...stationMap.values()].sort(
      (a, b) =>
        Number(b.Ridership ?? 0) - Number(a.Ridership ?? 0)
    );
  }, [statusRows]);

  const filteredStations = useMemo(
    () =>
      stations.filter(
        (row) =>
          String(row.Station || "")
            .toLowerCase()
            .includes(search.trim().toLowerCase()) &&
          (demandFilter === "All" ||
            String(row["Demand Status"] || "").toLowerCase() ===
              demandFilter.toLowerCase())
      ),
    [stations, search, demandFilter]
  );

  const summary = useMemo(
    () => ({
      stations: new Set(
        statusRows.map((row) => row.Station).filter(Boolean)
      ).size,
      high: statusRows.filter(
        (row) => demandClass(row["Demand Status"]) === "high"
      ).length,
      moderate: statusRows.filter(
        (row) => demandClass(row["Demand Status"]) === "moderate"
      ).length,
      peak: hotspots[0] || null,
    }),
    [statusRows, hotspots]
  );

  const heatmap = useMemo(() => {
    const map = new Map();

    heatmapRows.forEach((row) => {
      const hour = Number(row.Hour);

      if (
        !row.Station ||
        !Number.isInteger(hour) ||
        hour < 0 ||
        hour > 23
      ) {
        return;
      }

      if (!map.has(row.Station)) {
        map.set(row.Station, new Map());
      }

      map.get(row.Station).set(hour, row);
    });

    return [...map.entries()]
      .filter(([station]) =>
        station
          .toLowerCase()
          .includes(heatmapSearch.trim().toLowerCase())
      )
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([station, hours]) => ({ station, hours }));
  }, [heatmapRows, heatmapSearch]);

  const heatmapSummary = useMemo(() => {
    const rows =
      selectedHeatmapHour === "All"
        ? heatmapRows
        : heatmapRows.filter(
            (row) => Number(row.Hour) === Number(selectedHeatmapHour)
          );

    return {
      low: rows.filter(
        (row) => demandClass(row["Demand Status"]) === "low"
      ).length,
      moderate: rows.filter(
        (row) => demandClass(row["Demand Status"]) === "moderate"
      ).length,
      high: rows.filter(
        (row) => demandClass(row["Demand Status"]) === "high"
      ).length,
    };
  }, [heatmapRows, selectedHeatmapHour]);

  const availableStations = useMemo(
    () =>
      [
        ...new Set(
          statusRows.map((row) => row.Station).filter(Boolean)
        ),
      ].sort((a, b) => a.localeCompare(b)),
    [statusRows]
  );

  const selectedHourRow = useMemo(
    () =>
      statusRows.find(
        (row) =>
          row.Station === selectedStation &&
          Number(row.Hour) === Number(selectedStationHour)
      ) || null,
    [statusRows, selectedStation, selectedStationHour]
  );

  const stationPressure = useMemo(
    () =>
      pressureRows.find(
        (row) =>
          row.Station === selectedStation &&
          Number(row.Hour) === Number(selectedStationHour)
      ) || null,
    [pressureRows, selectedStation, selectedStationHour]
  );

  const busiestHour = useMemo(
    () =>
      statusRows
        .filter((row) => row.Station === selectedStation)
        .reduce(
          (best, row) =>
            !best ||
            Number(row.Ridership ?? 0) >
              Number(best.Ridership ?? 0)
              ? row
              : best,
          null
        ),
    [statusRows, selectedStation]
  );

  // Aggregate historical entries/exits for the selected station (all hours).
  const selectedFlow = useMemo(
    () => flows.find((row) => row.Station === selectedStation) || null,
    [flows, selectedStation]
  );

  const selectedNetFlow = finite(selectedFlow?.["Net Flow"]);

  const liveRows = useMemo(
    () =>
      [...(liveMonitoring?.station_snapshots || [])].sort(
        (a, b) =>
          (finite(pressure(b)) ?? -1) -
          (finite(pressure(a)) ?? -1)
      ),
    [liveMonitoring]
  );

  const liveHighCount =
    finite(liveMonitoring?.high_pressure_stations) ??
    liveRows.filter((row) =>
      ["high", "critical"].includes(
        String(pressureLevel(row)).toLowerCase()
      )
    ).length;

  const pressureCounts =
    networkOperations?.monitoring?.pressure_levels ||
    networkOperations?.pressure_counts ||
    {};

  const operations = networkOperations?.monitoring || {};

  const attentionRows =
    networkOperations?.high_pressure_station_list ||
    operations.high_pressure_station_list ||
    (operations.station_snapshots || []).filter(
      (row) => (finite(pressure(row)) ?? -1) >= 60
    );

  // The forecast must start after the latest observation the model can use,
  // and the backend allows at most 90 days beyond it.
  const forecastBase = predictionTiming(stationPrediction);
  const forecastMinDate = forecastBase?.targetDate ?? "";
  const forecastMaxDate = forecastBase
    ? shiftIsoDate(forecastBase.sourceDate, 90)
    : "";
  const forecastShownDate = forecastDate || forecastMinDate;

  const forecastHistoricalRow = forecastResult
    ? statusRows.find(
        (row) =>
          row.Station === selectedStation &&
          Number(row.Hour) === Number(forecastResult.target_hour)
      ) || null
    : null;

  if (loading) {
    return (
      <main className="station-intelligence-page">
        <div className="station-loading">
          <Activity size={24} />
          <p>Loading crowd monitoring data...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="station-intelligence-page">
      <header className="station-page-header">
        <div className="station-header-content">
          <div className="station-eyebrow">
            <span className="status-pulse" />
            AI METROFLOW / NETWORK INTELLIGENCE
          </div>

          <h1>Crowd Monitoring</h1>

          <p className="station-page-subtitle">
            Explore simulated station activity, AI demand estimates,
            historical hotspots, and passenger movement across the
            network.
          </p>
        </div>

        <div className="station-header-actions">
          <button
            type="button"
            className="station-refresh-button"
            onClick={() => loadCrowdData(true)}
            disabled={refreshing}
          >
            <RefreshCw
              size={16}
              className={refreshing ? "station-spin" : ""}
            />
            {refreshing ? "Refreshing..." : "Refresh History"}
          </button>

          <button
            type="button"
            className="station-refresh-button"
            onClick={exportCSV}
            disabled={
              !statusRows.length &&
              !hotspots.length &&
              !flows.length &&
              !heatmapRows.length &&
              !pressureRows.length
            }
          >
            <Download size={16} />
            Download CSV
          </button>
        </div>
      </header>

      {error && (
        <div className="station-error-notice" role="alert">
          <AlertTriangle size={17} />
          <span>{error}</span>
        </div>
      )}

      {/* Simulated activity: this is not a verified live BMRCL feed. */}
      <section className="station-panel">
        <div className="station-panel-header">
          <div className="station-panel-heading">
            <div className="station-eyebrow">
              SIMULATED NETWORK ACTIVITY
            </div>
            <h2>Simulated Live Network</h2>
            <p className="station-panel-description">
              Automatically refreshed demonstration activity based on a
              historical baseline. This is not a real BMRCL live feed.
            </p>
          </div>

          <div className="station-panel-icon blue">
            <Activity size={19} />
          </div>
        </div>

        <div className="station-error-notice" role="note">
          <AlertTriangle size={17} />
          <span>
            DEMO SIMULATION — activity values are simulated from
            historical monitoring results and are not verified current
            BMRCL passenger counts.
          </span>
        </div>

        {liveError && (
          <div className="station-error-notice" role="alert">
            <AlertTriangle size={17} />
            <span>{liveError}</span>
          </div>
        )}

        {!liveMonitoring && !liveError && (
          <div className="station-empty-cell">
            Loading simulated network activity...
          </div>
        )}

        {liveMonitoring && (
          <>
            <div className="station-metrics-grid">
              <MetricCard
                icon={MapPin}
                label="Stations Monitored"
                value={formatNumber(
                  liveMonitoring.stations_monitored ?? liveRows.length
                )}
                detail="Simulated station snapshots"
              />

              <MetricCard
                tone="orange"
                icon={AlertTriangle}
                label="High-Pressure Stations"
                value={formatNumber(liveHighCount)}
                detail="Analytical High/Critical classifications"
              />

              <MetricCard
                tone="purple"
                icon={Users}
                label="Highest Current Ridership"
                value={formatNumber(
                  currentRidership(
                    liveMonitoring.highest_current_ridership
                  )
                )}
                detail={stationName(
                  liveMonitoring.highest_current_ridership
                )}
              />

              <MetricCard
                tone="green"
                icon={TrendingUp}
                label="Highest Predicted Demand"
                value={formatNumber(
                  prediction(
                    liveMonitoring.highest_predicted_ridership
                  )
                )}
                detail={stationName(
                  liveMonitoring.highest_predicted_ridership
                )}
              />
            </div>

            <p className="station-panel-description">
              <strong>Last successful frontend update:</strong>{" "}
              {liveUpdatedAt?.toLocaleTimeString() || "Waiting"}
              {" · "}
              <strong>Simulation timestamp:</strong>{" "}
              {liveMonitoring.simulation_timestamp
                ? new Date(
                    liveMonitoring.simulation_timestamp
                  ).toLocaleTimeString()
                : "Unavailable"}
              {" · "}
              <strong>Historical baseline:</strong>{" "}
              {liveMonitoring.baseline_observation_date || "Unavailable"}
              {liveMonitoring.baseline_observation_hour != null
                ? ` at ${formatHour(
                    liveMonitoring.baseline_observation_hour
                  )}`
                : ""}
            </p>

            <div className="station-table-wrapper">
              <table className="station-data-table">
                <thead>
                  <tr>
                    <th>Station</th>
                    <th>Current Ridership</th>
                    <th>Entries</th>
                    <th>Exits</th>
                    <th>Net Flow</th>
                    <th>Predicted Demand</th>
                    <th>Pressure Score</th>
                    <th>Pressure Level</th>
                  </tr>
                </thead>

                <tbody>
                  {liveRows.map((row, index) => {
                    const entryCount = finite(entries(row));
                    const exitCount = finite(exits(row));

                    const netFlow =
                      finite(row.net_flow ?? row["Net Flow"]) ??
                      (entryCount !== null && exitCount !== null
                        ? entryCount - exitCount
                        : null);

                    const pressureScore = finite(pressure(row));

                    return (
                      <tr key={`${stationName(row)}-${index}`}>
                        <td>{stationName(row)}</td>
                        <td>{formatNumber(currentRidership(row))}</td>
                        <td>{formatNumber(entryCount)}</td>
                        <td>{formatNumber(exitCount)}</td>
                        <td>{formatNumber(netFlow)}</td>
                        <td>{formatNumber(prediction(row))}</td>
                        <td>
                          {pressureScore === null
                            ? "—"
                            : pressureScore.toFixed(1)}
                        </td>
                        <td>
                          <span
                            className={`station-risk-badge ${demandClass(
                              pressureLevel(row)
                            )}`}
                          >
                            {titleCase(pressureLevel(row))}
                          </span>
                        </td>
                      </tr>
                    );
                  })}

                  {!liveRows.length && (
                    <tr>
                      <td colSpan={8} className="station-empty-cell">
                        No simulated station snapshots are available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <p className="station-panel-description">
              Pressure scores are analytical indicators, not measured
              occupancy. The model is not retrained or independently
              rerun every five seconds.
            </p>
          </>
        )}
      </section>

      {/* Network-wide historical assessment */}
      <section className="station-panel">
        <div className="station-panel-header">
          <div className="station-panel-heading">
            <div className="station-eyebrow">
              NETWORK-WIDE AI DECISION SUPPORT
            </div>
            <h2>Network AI Operations</h2>
            <p className="station-panel-description">
              Historical-demand assessments and analytical pressure
              classifications; not verified real-time conditions.
            </p>
          </div>

          <div className="station-panel-icon blue">
            <Activity size={19} />
          </div>
        </div>

        {operationsError && (
          <div className="station-error-notice" role="alert">
            <AlertTriangle size={17} />
            <span>{operationsError}</span>
            <button
              type="button"
              className="station-refresh-button"
              onClick={loadOperations}
              disabled={operationsLoading}
            >
              Retry
            </button>
          </div>
        )}

        {operationsLoading && !networkOperations && (
          <div className="station-empty-cell">
            Loading network-wide AI operations...
          </div>
        )}

        {networkOperations && (
          <>
            <div className="station-metrics-grid">
              <MetricCard
                icon={MapPin}
                label="Stations Monitored"
                value={formatNumber(
                  operations.stations_monitored ??
                    networkOperations.stations_monitored
                )}
                detail="Historical assessment"
              />

              <MetricCard
                tone="orange"
                icon={AlertTriangle}
                label="High-Pressure Stations"
                value={formatNumber(
                  operations.high_pressure_stations ??
                    networkOperations.high_pressure_stations
                )}
                detail="Analytical pressure score ≥ 60"
              />

              <MetricCard
                tone="purple"
                icon={Users}
                label="Highest Current Ridership"
                value={formatNumber(
                  currentRidership(
                    operations.highest_current_ridership ||
                      networkOperations.highest_current_ridership
                  )
                )}
                detail={stationName(
                  operations.highest_current_ridership ||
                    networkOperations.highest_current_ridership
                )}
              />

              <MetricCard
                tone="green"
                icon={TrendingUp}
                label="Assessment Hour"
                value={formatHour(
                  operations.monitoring_hour ??
                    networkOperations.monitoring_hour
                )}
                detail={`Historical date: ${
                  operations.monitoring_date ||
                  networkOperations.monitoring_date ||
                  "Unavailable"
                }`}
              />
            </div>

            {(operations.highest_predicted_ridership ||
              networkOperations.highest_predicted_ridership) && (
              <p className="station-panel-description">
                <strong>Highest predicted demand:</strong>{" "}
                {stationName(
                  operations.highest_predicted_ridership ||
                    networkOperations.highest_predicted_ridership
                )}
                {" — "}
                {formatNumber(
                  prediction(
                    operations.highest_predicted_ridership ||
                      networkOperations.highest_predicted_ridership
                  )
                )}
                {" for the next-hour estimate."}
              </p>
            )}

            <h3 className="station-subsection-title">
              Network Pressure Classification
            </h3>

            <div className="station-metrics-grid">
              {["LOW", "MODERATE", "HIGH", "CRITICAL"].map(
                (level, index) => (
                  <MetricCard
                    key={level}
                    tone={["green", "blue", "orange", "purple"][index]}
                    label={titleCase(level)}
                    value={formatNumber(
                      pressureCounts[level] ??
                        pressureCounts[level.toLowerCase()] ??
                        0
                    )}
                    detail="Historical pressure records"
                  />
                )
              )}
            </div>

            <div className="station-panel-header">
              <div className="station-panel-heading">
                <h3>Stations Requiring Attention</h3>
                <p className="station-panel-description">
                  Stations identified by the backend analytical
                  pressure-score threshold.
                </p>
              </div>

              <button
                type="button"
                className="station-refresh-button"
                onClick={loadOperations}
                disabled={operationsLoading}
              >
                <RefreshCw
                  size={15}
                  className={operationsLoading ? "station-spin" : ""}
                />
                {operationsLoading
                  ? "Refreshing..."
                  : "Refresh Operations"}
              </button>
            </div>

            <div className="station-table-wrapper">
              <table className="station-data-table">
                <thead>
                  <tr>
                    <th>Station</th>
                    <th>Current Ridership</th>
                    <th>Predicted Demand</th>
                    <th>Pressure Score</th>
                    <th>Pressure Level</th>
                  </tr>
                </thead>

                <tbody>
                  {attentionRows.length ? (
                    attentionRows.map((row, index) => {
                      const score = finite(pressure(row));

                      return (
                        <tr key={`${stationName(row)}-${index}`}>
                          <td>{stationName(row)}</td>
                          <td>{formatNumber(currentRidership(row))}</td>
                          <td>{formatNumber(prediction(row))}</td>
                          <td>
                            {score === null ? "—" : score.toFixed(1)}
                          </td>
                          <td>
                            <span
                              className={`station-risk-badge ${demandClass(
                                pressureLevel(row)
                              )}`}
                            >
                              {titleCase(pressureLevel(row))}
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="station-empty-cell">
                        No high-pressure stations were identified for
                        this assessment.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      {/* Historical summary cards */}
      <section className="station-metrics-grid">
        <MetricCard
          icon={MapPin}
          label="Historical Stations"
          value={formatNumber(summary.stations)}
          detail="Unique stations in historical records"
        />

        <MetricCard
          tone="orange"
          icon={AlertTriangle}
          label="High-Demand Records"
          value={formatNumber(summary.high)}
          detail="Station × hour-of-day buckets classified High"
        />

        <MetricCard
          tone="purple"
          icon={Users}
          label="Moderate-Demand Records"
          value={formatNumber(summary.moderate)}
          detail="Station × hour-of-day buckets classified Moderate"
        />

        <MetricCard
          tone="green"
          icon={TrendingUp}
          label="Peak Historical Hotspot"
          value={summary.peak?.Station || "Unavailable"}
          detail={
            summary.peak
              ? `${formatNumber(summary.peak.Ridership)} total ridership · ${formatHour(summary.peak.Hour)}`
              : "No hotspot data"
          }
        />
      </section>

      {/* Station explorer with latest station-specific prediction */}
      <section className="station-panel">
        <div className="station-panel-header">
          <div className="station-panel-heading">
            <div className="station-eyebrow">
              STATION-LEVEL ANALYSIS
            </div>
            <h2>Station Congestion Explorer</h2>
            <p className="station-panel-description">
              Historical demand for the selected station and hour, plus
              a separately sourced latest-observation next-hour AI
              prediction.
            </p>
          </div>

          <div className="station-panel-icon blue">
            <Activity size={19} />
          </div>
        </div>

        <div className="crowd-heatmap-controls">
          <select
            className="station-filter-select"
            value={selectedStation}
            onChange={(event) => setSelectedStation(event.target.value)}
            aria-label="Select station"
          >
            <option value="">Select a station</option>

            {availableStations.map((station) => (
              <option key={station} value={station}>
                {station}
              </option>
            ))}
          </select>

          <select
            className="station-filter-select"
            value={selectedStationHour}
            onChange={(event) =>
              setSelectedStationHour(event.target.value)
            }
            aria-label="Select historical hour"
          >
            {Array.from({ length: 24 }, (_, hour) => (
              <option key={hour} value={String(hour)}>
                {formatHour(hour)}
              </option>
            ))}
          </select>
        </div>

        {!selectedStation ? (
          <div className="station-empty-cell">
            Select a station to explore historical demand and its latest
            available AI prediction.
          </div>
        ) : (
          <>
            <div className="station-metrics-grid">
              <MetricCard
                icon={MapPin}
                label="Selected Station"
                value={selectedStation}
                detail={`Historical hour: ${formatHour(selectedStationHour)}`}
              />

              <MetricCard
                tone="purple"
                icon={Users}
                label="Total Ridership at This Hour"
                value={formatNumber(selectedHourRow?.Ridership)}
                detail="Summed over all dates in the dataset"
              />

              <MetricCard
                tone="green"
                icon={Users}
                label="Average Ridership at This Hour"
                value={formatNumber(
                  selectedHourRow?.["Average Daily Ridership"]
                )}
                detail={
                  selectedHourRow?.["Days Observed"] != null
                    ? `Per observed day · ${formatNumber(
                        selectedHourRow["Days Observed"]
                      )} days observed`
                    : "Per-day average unavailable"
                }
              />

              <MetricCard
                tone="orange"
                icon={Activity}
                label="Relative Demand"
                value={
                  <span
                    className={`station-risk-badge ${demandClass(
                      selectedHourRow?.["Demand Status"]
                    )}`}
                  >
                    {titleCase(selectedHourRow?.["Demand Status"])}
                  </span>
                }
                detail="Relative to this station's own 24 hourly totals"
              />

              <MetricCard
                icon={Activity}
                label="Relative Pressure"
                value={
                  finite(stationPressure?.["Demand Pressure"]) === null
                    ? "—"
                    : `${finite(
                        stationPressure?.["Demand Pressure"]
                      ).toFixed(2)} / 100`
                }
                detail="Historical analytical score, not occupancy"
              />

              <MetricCard
                tone="purple"
                icon={Users}
                label="Station Average"
                value={formatNumber(
                  stationPressure?.["Station Average Ridership"] == null
                    ? null
                    : Math.round(
                        Number(
                          stationPressure["Station Average Ridership"]
                        )
                      )
                )}
                detail="Mean of this station's 24 hourly totals"
              />

              <MetricCard
                tone="orange"
                icon={TrendingUp}
                label="Demand vs Average"
                value={
                  finite(stationPressure?.["Demand vs Average (%)"]) ===
                  null
                    ? "—"
                    : `${
                        finite(
                          stationPressure["Demand vs Average (%)"]
                        ) > 0
                          ? "+"
                          : ""
                      }${finite(
                        stationPressure["Demand vs Average (%)"]
                      ).toFixed(2)}%`
                }
                detail="Historical comparison"
              />

              <MetricCard
                tone="green"
                icon={TrendingUp}
                label="Busiest Recorded Hour"
                value={formatHour(busiestHour?.Hour)}
                detail={
                  busiestHour
                    ? `${formatNumber(busiestHour.Ridership)} total · ${formatNumber(
                        busiestHour["Average Daily Ridership"]
                      )} avg per observed day`
                    : "No hourly data"
                }
              />

              <MetricCard
                tone="green"
                icon={ArrowRightLeft}
                label="Total Entries"
                value={formatNumber(selectedFlow?.Ridership_entry)}
                detail="Aggregate across all hours in the dataset"
              />

              <MetricCard
                tone="orange"
                icon={ArrowRightLeft}
                label="Total Exits"
                value={formatNumber(selectedFlow?.Ridership_exit)}
                detail="Aggregate across all hours in the dataset"
              />

              <MetricCard
                tone="purple"
                icon={ArrowRightLeft}
                label="Net Passenger Flow"
                value={
                  selectedNetFlow === null
                    ? "—"
                    : `${selectedNetFlow > 0 ? "+" : ""}${formatNumber(
                        selectedNetFlow
                      )}`
                }
                detail="Entries minus exits; positive means more entries"
              />
            </div>

            <h3 className="station-subsection-title">
              Latest Available Next-Hour AI Prediction
            </h3>

            <p className="station-panel-description">
              This prediction uses the latest historical observation
              available for the selected station. It is not a prediction
              specifically for the historical hour selected above.
            </p>

            {predictionLoading && (
              <div className="station-empty-cell">
                Loading station prediction...
              </div>
            )}

            {predictionError && (
              <div className="station-error-notice" role="alert">
                <AlertTriangle size={17} />
                <span>{predictionError}</span>
              </div>
            )}

            {stationPrediction && !predictionLoading && (
              <>
                <div className="station-metrics-grid">
                  <MetricCard
                    tone="green"
                    icon={TrendingUp}
                    label="Predicted Next-Hour Ridership"
                    value={formatNumber(prediction(stationPrediction))}
                    detail={
                      stationPrediction.station ||
                      stationName(stationPrediction) ||
                      selectedStation
                    }
                  />

                  <MetricCard
                    icon={Activity}
                    label="Latest Observation Used"
                    value={
                      predictionTiming(stationPrediction)?.sourceDate ??
                      "Not provided"
                    }
                    detail={
                      predictionTiming(stationPrediction)
                        ? `Observed hour: ${formatHour(
                            predictionTiming(stationPrediction).sourceHour
                          )}`
                        : "Source time was not returned"
                    }
                  />

                  <MetricCard
                    tone="purple"
                    icon={TrendingUp}
                    label="Prediction Target"
                    value={
                      predictionTiming(stationPrediction)
                        ? formatHour(
                            predictionTiming(stationPrediction).targetHour
                          )
                        : "Not provided"
                    }
                    detail={
                      predictionTiming(stationPrediction)
                        ? `Target date: ${
                            predictionTiming(stationPrediction).targetDate
                          }`
                        : "Target time was not returned"
                    }
                  />

                  <MetricCard
                    tone="orange"
                    icon={AlertTriangle}
                    label="Data Mode"
                    value={
                      stationPrediction.is_simulated_data == null
                        ? "Not provided"
                        : stationPrediction.is_simulated_data
                        ? "Simulated demo dates"
                        : "Historical dataset"
                    }
                    detail={
                      stationPrediction.is_live_data === false
                        ? "Not a live feed"
                        : "Live status not reported"
                    }
                  />
                </div>

                <p className="station-panel-description">
                  The estimate is model-generated from the latest
                  available historical observation and should not be
                  interpreted as verified real-time ridership.
                  {stationPrediction.prediction_note
                    ? ` ${stationPrediction.prediction_note}`
                    : ""}
                </p>
              </>
            )}

            <h3 className="station-subsection-title">
              Future Hourly Forecast (Trained XGBoost Model)
            </h3>

            <p className="station-panel-description">
              Choose a target date and hour. The trained model is rolled
              forward hour by hour from the last observation in the
              dataset
              {forecastBase
                ? ` (${forecastBase.sourceDate} ${formatHour(
                    forecastBase.sourceHour
                  )})`
                : ""}
              , up to 90 days ahead. Dates inside the historical data
              cannot be forecast with this tool.
            </p>

            <div className="crowd-heatmap-controls">
              <input
                className="station-search-input"
                type="date"
                style={{ colorScheme: "dark" }}
                value={forecastShownDate}
                min={forecastMinDate || undefined}
                max={forecastMaxDate || undefined}
                onChange={(event) => setForecastDate(event.target.value)}
                disabled={!forecastBase}
                aria-label="Forecast target date"
              />

              <select
                className="station-filter-select"
                value={forecastHour}
                onChange={(event) => setForecastHour(event.target.value)}
                disabled={!forecastBase}
                aria-label="Forecast target hour"
              >
                {Array.from({ length: 24 }, (_, hour) => (
                  <option key={hour} value={String(hour)}>
                    {formatHour(hour)}
                  </option>
                ))}
              </select>

              <button
                type="button"
                className="station-refresh-button"
                onClick={runForecast}
                disabled={!forecastBase || forecastLoading}
              >
                <TrendingUp size={15} />
                {forecastLoading ? "Forecasting..." : "Run Forecast"}
              </button>
            </div>

            {!forecastBase && !predictionLoading && (
              <div className="station-empty-cell">
                The forecast controls are enabled once the latest
                observation for this station has loaded.
              </div>
            )}

            {forecastLoading && (
              <div className="station-empty-cell">
                Rolling the model forward... distant dates can take a few
                seconds.
              </div>
            )}

            {forecastError && (
              <div className="station-error-notice" role="alert">
                <AlertTriangle size={17} />
                <span>{forecastError}</span>
              </div>
            )}

            {forecastResult && !forecastLoading && (
              <>
                <div className="station-metrics-grid">
                  <MetricCard
                    tone="green"
                    icon={TrendingUp}
                    label="Forecast Ridership"
                    value={formatNumber(forecastResult.predicted_ridership)}
                    detail={`${forecastResult.target_date} ${formatHour(
                      forecastResult.target_hour
                    )} · ${forecastResult.station || selectedStation}`}
                  />

                  <MetricCard
                    tone="purple"
                    icon={Activity}
                    label="Hours Ahead"
                    value={formatNumber(forecastResult.forecast_steps)}
                    detail={`Rolled forward from ${
                      forecastResult.latest_station_observation ||
                      "the latest observation"
                    }`}
                  />

                  <MetricCard
                    tone="orange"
                    icon={Users}
                    label="Historical Average, Same Hour"
                    value={formatNumber(
                      forecastHistoricalRow?.["Average Daily Ridership"]
                    )}
                    detail="Per observed day; context only, not a target"
                  />

                  <MetricCard
                    icon={AlertTriangle}
                    label="Forecast Method"
                    value={forecastResult.model || "Model"}
                    detail="Recursive forecast; exits use historical hourly medians"
                  />
                </div>

                <p className="station-panel-description">
                  This is a model forecast, not an observed or live
                  passenger count.{" "}
                  {forecastResult.is_simulated_data
                    ? "Dates are simulated demo dates. "
                    : "It is based on the historical dataset. "}
                  Each hour is predicted from the previous hour's
                  predicted value, so errors build up and accuracy falls
                  the further ahead you go. The model's reported test
                  metrics were measured for single next-hour predictions
                  and do not describe these multi-step forecasts.
                  {forecastResult.note ? ` ${forecastResult.note}` : ""}
                </p>
              </>
            )}
          </>
        )}
      </section>

      {/* Historical heatmap */}
      <section className="station-panel">
        <div className="station-panel-header">
          <div className="station-panel-heading">
            <div className="station-eyebrow">
              HISTORICAL DEMAND PATTERNS
            </div>
            <h2>Crowd Heatmap</h2>
            <p className="station-panel-description">
              Historical demand classifications across stations and
              hours. Each cell compares an hour-of-day total with the
              same station's other hours. Cells are not live
              observations.
            </p>
          </div>

          <div className="station-panel-icon blue">
            <Grid3X3 size={19} />
          </div>
        </div>

        <div className="crowd-heatmap-controls">
          <input
            className="station-search-input"
            type="search"
            value={heatmapSearch}
            onChange={(event) => setHeatmapSearch(event.target.value)}
            placeholder="Search heatmap station..."
            aria-label="Search heatmap station"
          />

          <select
            className="station-filter-select"
            value={selectedHeatmapHour}
            onChange={(event) =>
              setSelectedHeatmapHour(event.target.value)
            }
            aria-label="Filter heatmap by hour"
          >
            <option value="All">All hours</option>

            {Array.from({ length: 24 }, (_, hour) => (
              <option key={hour} value={String(hour)}>
                {formatHour(hour)}
              </option>
            ))}
          </select>

          <span className="station-count-pill">
            {heatmap.length} stations
          </span>
        </div>

        <div className="crowd-heatmap-legend">
          <span>
            <i className="heatmap-low" />
            Low
          </span>
          <span>
            <i className="heatmap-moderate" />
            Moderate
          </span>
          <span>
            <i className="heatmap-high" />
            High
          </span>
          <span>
            <i className="heatmap-unknown" />
            No data
          </span>
        </div>

        <div className="crowd-heatmap-summary">
          <div>
            <span className="heatmap-low" />
            <strong>{formatNumber(heatmapSummary.low)}</strong>
            <small>Low cells</small>
          </div>

          <div>
            <span className="heatmap-moderate" />
            <strong>{formatNumber(heatmapSummary.moderate)}</strong>
            <small>Moderate cells</small>
          </div>

          <div>
            <span className="heatmap-high" />
            <strong>{formatNumber(heatmapSummary.high)}</strong>
            <small>High cells</small>
          </div>
        </div>

        <div className="crowd-heatmap-scroll">
          {heatmap.length ? (
            <table className="crowd-heatmap-table">
              <thead>
                <tr>
                  <th className="heatmap-station-heading">Station</th>

                  {Array.from({ length: 24 }, (_, hour) => (
                    <th
                      key={hour}
                      className={
                        selectedHeatmapHour !== "All" &&
                        Number(selectedHeatmapHour) === hour
                          ? "heatmap-selected-hour"
                          : ""
                      }
                    >
                      {String(hour).padStart(2, "0")}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {heatmap.map(({ station, hours }) => (
                  <tr key={station}>
                    <th className="heatmap-station-heading">
                      {station}
                    </th>

                    {Array.from({ length: 24 }, (_, hour) => {
                      const row = hours.get(hour);
                      const className = demandClass(
                        row?.["Demand Status"]
                      );

                      const selected =
                        selectedHeatmapHour !== "All" &&
                        Number(selectedHeatmapHour) === hour;

                      return (
                        <td
                          key={hour}
                          className={
                            selected ? "heatmap-selected-column" : ""
                          }
                        >
                          <span
                            className={`heatmap-cell ${
                              row ? className : "unknown"
                            }`}
                            title={
                              row
                                ? `${station} · ${formatHour(hour)} · ${formatNumber(
                                    row.Ridership
                                  )} total ridership (all dates) · ${row["Demand Status"]}`
                                : `${station} · ${formatHour(hour)} · No data`
                            }
                            aria-label={
                              row
                                ? `${station}, ${formatHour(hour)}, ${
                                    row["Demand Status"]
                                  }, ${formatNumber(row.Ridership)} total ridership`
                                : `${station}, ${formatHour(hour)}, no data`
                            }
                          />
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="station-empty-cell">
              {heatmapRows.length
                ? "No stations match your search."
                : "Historical heatmap data is unavailable."}
            </div>
          )}
        </div>
      </section>

      {/* Station peak demand */}
      <section className="station-panel">
        <div className="station-panel-header">
          <div className="station-panel-heading">
            <div className="station-eyebrow">
              HISTORICAL NETWORK DEMAND
            </div>
            <h2>Station Peak Demand</h2>
            <p className="station-panel-description">
              Each station's busiest hour of day, by total ridership
              summed over all dates in the dataset.
            </p>
          </div>

          <div className="station-panel-icon blue">
            <Activity size={19} />
          </div>
        </div>

        <div className="station-table-controls">
          <span className="station-count-pill">
            {filteredStations.length} stations
          </span>

          <input
            className="station-search-input"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search station..."
            aria-label="Search station"
          />

          <select
            className="station-filter-select"
            value={demandFilter}
            onChange={(event) => setDemandFilter(event.target.value)}
            aria-label="Filter by demand status"
          >
            <option value="All">All demand levels</option>
            <option value="High">High</option>
            <option value="Moderate">Moderate</option>
            <option value="Low">Low</option>
          </select>
        </div>

        <div className="station-table-wrapper">
          <table className="station-data-table">
            <thead>
              <tr>
                <th>Station</th>
                <th>Peak Recorded Hour</th>
                <th>Total Ridership (all dates)</th>
                <th>Avg per Observed Day</th>
                <th>Relative Status at That Hour</th>
              </tr>
            </thead>

            <tbody>
              {filteredStations.length ? (
                filteredStations.map((row) => (
                  <tr key={row.Station}>
                    <td>{row.Station}</td>
                    <td>{formatHour(row.Hour)}</td>
                    <td>{formatNumber(row.Ridership)}</td>
                    <td>{formatNumber(row["Average Daily Ridership"])}</td>
                    <td>
                      <span
                        className={`station-risk-badge ${demandClass(
                          row["Demand Status"]
                        )}`}
                      >
                        {titleCase(row["Demand Status"])}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="station-empty-cell">
                    No stations match the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Historical hotspots */}
      <section className="station-panel">
        <div className="station-panel-header">
          <div className="station-panel-heading">
            <div className="station-eyebrow">
              HISTORICAL HIGH-DEMAND LOCATIONS
            </div>
            <h2>Historical Crowd Hotspots</h2>
            <p className="station-panel-description">
              Highest station × hour-of-day ridership totals, each
              summed over all dates in the dataset. A station may appear
              more than once at different hours.
            </p>
          </div>

          <div className="station-panel-icon red">
            <TrendingUp size={19} />
          </div>
        </div>

        <div className="station-table-wrapper">
          <table className="station-data-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Station</th>
                <th>Hour</th>
                <th>Total Ridership (all dates)</th>
                <th>Avg per Observed Day</th>
              </tr>
            </thead>

            <tbody>
              {hotspots.length ? (
                hotspots.map((row, index) => (
                  <tr key={`${row.Station}-${row.Hour}-${index}`}>
                    <td>{index + 1}</td>
                    <td>{row.Station}</td>
                    <td>{formatHour(row.Hour)}</td>
                    <td>{formatNumber(row.Ridership)}</td>
                    <td>{formatNumber(row["Average Daily Ridership"])}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="station-empty-cell">
                    No historical hotspot data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Passenger flow */}
      <section className="station-panel">
        <div className="station-panel-header">
          <div className="station-panel-heading">
            <div className="station-eyebrow">
              HISTORICAL PASSENGER MOVEMENT
            </div>
            <h2>Station Passenger Flow</h2>
            <p className="station-panel-description">
              Aggregate historical entries, exits, and net flow.
              Positive net flow means entries exceed exits; negative
              net flow means exits exceed entries.
            </p>
          </div>

          <div className="station-panel-icon purple">
            <ArrowRightLeft size={19} />
          </div>
        </div>

        <div className="station-table-wrapper">
          <table className="station-data-table">
            <thead>
              <tr>
                <th>Station</th>
                <th>Entries</th>
                <th>Exits</th>
                <th>Net Flow</th>
              </tr>
            </thead>

            <tbody>
              {flows.length ? (
                flows.map((row, index) => {
                  const net = finite(row["Net Flow"]) ?? 0;

                  return (
                    <tr key={`${row.Station}-${index}`}>
                      <td>{row.Station}</td>
                      <td>{formatNumber(row.Ridership_entry)}</td>
                      <td>{formatNumber(row.Ridership_exit)}</td>
                      <td>
                        <span
                          className={
                            net >= 0
                              ? "station-flow-positive"
                              : "station-flow-negative"
                          }
                        >
                          {formatNumber(net)}
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={4} className="station-empty-cell">
                    No historical passenger-flow data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <footer className="station-page-footer">
        <span>
          <Activity size={14} />
          AI MetroFlow · Crowd Monitoring
        </span>
      </footer>
    </main>
  );
}

export default CrowdMonitoring;
