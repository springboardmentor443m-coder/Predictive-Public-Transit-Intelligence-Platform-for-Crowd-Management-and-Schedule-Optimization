import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import api from "../services/api";
import "../styles/DemandPulse.css";

const LIVE_INTERVAL = 15000;
const DEFAULT_FORECAST_DATE = "2026-10-15";
const PAGE_SIZE = 12;
const INITIAL_ALERTS = 5;

const SEVERITY_ORDER = {
  CRITICAL: 4,
  HIGH: 3,
  MODERATE: 2,
  LOW: 1,
};

const formatNumber = (value, digits = 0) =>
  value == null || value === "" || !Number.isFinite(Number(value))
    ? "—"
    : Number(value).toLocaleString("en-IN", {
        maximumFractionDigits: digits,
        minimumFractionDigits: digits,
      });

const getSeverity = (station) =>
  String(station?.congestion_level || "LOW").toUpperCase();

const getPriorityClass = (severity) =>
  String(severity || "LOW").toLowerCase();

const getAlertValue = (alert) => {
  const error = alert.prediction_error_percentage;
  const pressure = alert.monitoring_data?.pressure_score;

  if (error != null) return `${formatNumber(error, 2)}% error`;
  if (pressure != null) return `${formatNumber(pressure, 2)} pressure`;

  return alert.alert_type || "Station alert";
};

function MetricCard({ label, value, detail, tone = "" }) {
  return (
    <article className="demand-stat-card">
      <span className="stat-label">{label}</span>
      <strong className={tone}>{value}</strong>
      {detail && (
        <span className="stat-description">{detail}</span>
      )}
    </article>
  );
}

function StationCard({ station, onView }) {
  const severity = getSeverity(station);

  const pressure = Math.max(
    0,
    Math.min(100, Number(station.pressure_score) || 0)
  );

  return (
    <article
      className={`station-card station-card-${getPriorityClass(
        severity
      )}`}
    >
      <div className="station-card-top">
        <span className="station-card-icon" aria-hidden="true">
          <span className="station-card-dot" />
        </span>

        <span
          className={`priority-badge priority-${getPriorityClass(
            severity
          )}`}
        >
          {severity}
        </span>
      </div>

      <h3 className="station-card-name">
        {station.station}
      </h3>

      <div className="station-card-pressure">
        <span>Pressure score</span>
        <strong>
          {formatNumber(station.pressure_score, 2)}
        </strong>
      </div>

      <div className="station-pressure-track">
        <span
          className={`station-pressure-fill pressure-fill-${getPriorityClass(
            severity
          )}`}
          style={{ width: `${pressure}%` }}
        />
      </div>

      <div className="station-card-metrics">
        <div>
          <span>Entries</span>
          <strong>
            {formatNumber(station.current_ridership)}
          </strong>
        </div>

        <div>
          <span>Exits</span>
          <strong>
            {formatNumber(station.current_exit)}
          </strong>
        </div>

        <div>
          <span>Net flow</span>
          <strong>{formatNumber(station.net_flow)}</strong>
        </div>

        <div>
          <span>Next-hour prediction</span>
          <strong>
            {formatNumber(
              station.predicted_next_hour_ridership
            )}
          </strong>
        </div>
      </div>

      <div className="station-card-footer">
        <span className="station-card-error">
          Error:{" "}
          {formatNumber(
            station.prediction_error_percentage,
            2
          )}
          %
        </span>

        <button
          className="station-detail-button"
          onClick={() => onView(station.station)}
          type="button"
        >
          View details <span aria-hidden="true">→</span>
        </button>
      </div>
    </article>
  );
}

function AlertCard({ alert, index }) {
  const [expanded, setExpanded] = useState(false);

  const severity = String(
    alert.severity || "LOW"
  ).toUpperCase();

  return (
    <article
      className={`monitoring-alert-card alert-card-${getPriorityClass(
        severity
      )}`}
    >
      <button
        className="monitoring-alert-trigger"
        type="button"
        aria-expanded={expanded}
        onClick={() =>
          setExpanded((value) => !value)
        }
      >
        <span className="monitoring-alert-number">
          {String(index + 1).padStart(2, "0")}
        </span>

        <span className="monitoring-alert-content">
          <strong>
            {alert.station ||
              alert.title ||
              "Network alert"}
          </strong>

          <span>
            {alert.title ||
              alert.alert_type ||
              "Station alert"}
          </span>

          <small>{getAlertValue(alert)}</small>
        </span>

        <span
          className={`priority-badge priority-${getPriorityClass(
            severity
          )}`}
        >
          {severity}
        </span>

        <span
          className={`monitoring-alert-chevron ${
            expanded ? "is-expanded" : ""
          }`}
        >
          ⌄
        </span>
      </button>

      {expanded && (
        <div className="monitoring-alert-details">
          {alert.message && <p>{alert.message}</p>}

          {alert.recommendation && (
            <div>
              <span>Recommended action</span>
              <p>{alert.recommendation}</p>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

export default function DemandPulse() {
  const [monitoring, setMonitoring] = useState(null);
  const [search, setSearch] = useState("");
  const [pressureFilter, setPressureFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState("pressure");
  const [selectedStation, setSelectedStation] = useState("");
  const [page, setPage] = useState(1);
  const [showAllAlerts, setShowAllAlerts] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const [forecastDate, setForecastDate] = useState(
    DEFAULT_FORECAST_DATE
  );
  const [demandForecast, setDemandForecast] = useState(null);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastError, setForecastError] = useState("");

  const requestInProgress = useRef(false);
  const mounted = useRef(false);

  const loadDemandForecast = useCallback(
    async (targetDate) => {
      if (!targetDate) return;

      setForecastLoading(true);
      setForecastError("");

      try {
        const response = await api.get(
          `/prediction/demand/date/${encodeURIComponent(
            targetDate
          )}`
        );

        setDemandForecast(response.data);
      } catch (err) {
        setForecastError(
          err?.response?.data?.detail ||
            err?.message ||
            "Unable to load the daily demand forecast."
        );

        setDemandForecast(null);
      } finally {
        setForecastLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    loadDemandForecast(DEFAULT_FORECAST_DATE);
  }, [loadDemandForecast]);

  const loadData = useCallback(async () => {
    if (requestInProgress.current) return;

    requestInProgress.current = true;
    setRefreshing(true);

    try {
      setError("");

      // Uses the authenticated Axios client and its existing token handling.
      const response = await api.get("/monitoring/live");
      const result = response.data;

      if (
        !result ||
        !Array.isArray(result.station_snapshots)
      ) {
        throw new Error(
          "The monitoring endpoint returned an unexpected response."
        );
      }

      if (mounted.current) {
        setMonitoring(result);
        setLastUpdated(new Date());
      }
    } catch (err) {
      if (mounted.current) {
        setError(
          err?.response?.data?.detail ||
            err?.message ||
            "Unable to retrieve monitoring data."
        );
      }
    } finally {
      requestInProgress.current = false;

      if (mounted.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  // Fetch the monitoring snapshot and refresh it periodically.
  useEffect(() => {
    mounted.current = true;

    loadData();

    const intervalId = window.setInterval(() => {
      loadData();
    }, LIVE_INTERVAL);

    return () => {
      mounted.current = false;
      window.clearInterval(intervalId);
    };
  }, [loadData]);

  const allStations = monitoring?.station_snapshots || [];

  const stations = useMemo(() => {
    const query = search.trim().toLowerCase();

    return [...allStations]
      .filter((station) =>
        String(station.station || "")
          .toLowerCase()
          .includes(query)
      )
      .filter(
        (station) =>
          pressureFilter === "ALL" ||
          getSeverity(station) === pressureFilter
      )
      .sort((a, b) => {
        if (sortBy === "ridership") {
          return (
            Number(b.current_ridership || 0) -
            Number(a.current_ridership || 0)
          );
        }

        if (sortBy === "prediction") {
          return (
            Number(
              b.predicted_next_hour_ridership || 0
            ) -
            Number(
              a.predicted_next_hour_ridership || 0
            )
          );
        }

        if (sortBy === "flow") {
          return (
            Number(b.net_flow || 0) -
            Number(a.net_flow || 0)
          );
        }

        return (
          (SEVERITY_ORDER[getSeverity(b)] || 0) -
            (SEVERITY_ORDER[getSeverity(a)] || 0) ||
          Number(b.pressure_score || 0) -
            Number(a.pressure_score || 0)
        );
      });
  }, [allStations, search, pressureFilter, sortBy]);

  const totalPages = Math.max(
    1,
    Math.ceil(stations.length / PAGE_SIZE)
  );

  const visibleStations = stations.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );

  useEffect(() => {
    setPage(1);
  }, [search, pressureFilter, sortBy]);

  const stationDetails = useMemo(
    () =>
      allStations.find(
        (station) =>
          station.station === selectedStation
      ) || null,
    [allStations, selectedStation]
  );

  const pressureLevels = monitoring?.pressure_levels || {};

  const snapshotPressureCounts = useMemo(() => {
    const counts = {
      LOW: 0,
      MODERATE: 0,
      HIGH: 0,
      CRITICAL: 0,
    };

    allStations.forEach((station) => {
      const severity = getSeverity(station);

      if (severity in counts) {
        counts[severity] += 1;
      }
    });

    return counts;
  }, [allStations]);

  console.log("MetroFlow pressure diagnostic:", {
    apiPressureLevels: pressureLevels,
    snapshotPressureCounts,
    stationsMonitored: monitoring?.stations_monitored,
    snapshotsReceived: allStations.length,
  });

  const highest =
    monitoring?.highest_current_ridership || null;

  // Derive analytical pressure alerts from the monitoring snapshot.
  const alerts = useMemo(() => {
    return allStations
      .filter((station) => {
        const level = getSeverity(station);

        return (
          level === "HIGH" ||
          level === "CRITICAL"
        );
      })
      .map((station) => ({
        station: station.station,
        severity: getSeverity(station),
        alert_type: "CROWD_PRESSURE",
        title: `${getSeverity(station)} crowd pressure`,
        message: `Analytical pressure score is ${formatNumber(
          station.pressure_score,
          2
        )}.`,
        recommendation:
          getSeverity(station) === "CRITICAL"
            ? "Prioritize station monitoring and consider operational intervention."
            : "Monitor passenger flows and review service capacity.",
        monitoring_data: {
          pressure_score: station.pressure_score,
        },
      }))
      .sort(
        (a, b) =>
          (SEVERITY_ORDER[b.severity] || 0) -
            (SEVERITY_ORDER[a.severity] || 0) ||
          Number(b.monitoring_data.pressure_score) -
            Number(a.monitoring_data.pressure_score)
      );
  }, [allStations]);

  const severityCounts = useMemo(() => {
    const counts = {
      CRITICAL: 0,
      HIGH: 0,
      MODERATE: 0,
      LOW: 0,
    };

    allStations.forEach((station) => {
      const severity = getSeverity(station);

      if (severity in counts) {
        counts[severity] += 1;
      }
    });

    return counts;
  }, [allStations]);

  const visibleAlerts = showAllAlerts
    ? alerts
    : alerts.slice(0, INITIAL_ALERTS);

  useEffect(() => {
    if (!stationDetails) return;

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setSelectedStation("");
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () =>
      window.removeEventListener(
        "keydown",
        handleKeyDown
      );
  }, [stationDetails]);

  if (loading && !monitoring) {
    return (
      <main className="demand-pulse-page">
        <div className="demand-loading-card">
          <div className="loading-spinner" />
          <h2>Loading network monitoring</h2>
        </div>
      </main>
    );
  }

  if (error && !monitoring) {
    return (
      <main className="demand-pulse-page">
        <div className="demand-error-card">
          <h2>Unable to load network monitoring</h2>
          <p>{error}</p>

          <button
            className="retry-button"
            onClick={loadData}
            type="button"
          >
            Try again
          </button>
        </div>
      </main>
    );
  }

  const relatedAlerts = stationDetails
    ? alerts.filter(
        (alert) =>
          alert.station === stationDetails.station
      )
    : [];

  return (
    <main className="demand-pulse-page">
      <header className="demand-page-header">
        <div>
          <span className="page-eyebrow">
            AI METROFLOW / OPERATIONS
          </span>

          <h1>Network Monitoring</h1>

          <p>
            Historical passenger observations and ML-based
            demand predictions, analytical pressure scores
            and station alerts.
          </p>

          <span className="monitoring-period">
            Historical dataset · latest available observations
          </span>
        </div>

        <div className="monitoring-controls">
          <button
            className="retry-button"
            onClick={loadData}
            disabled={refreshing}
            type="button"
          >
            {refreshing ? "Updating…" : "Update now"}
          </button>
        </div>
      </header>

      {error && (
        <div className="monitoring-inline-error" role="alert">
          {error} Showing the most recent successful snapshot
          while retrying.
        </div>
      )}

      <section
        className="demand-section"
        aria-labelledby="daily-forecast-heading"
      >
        <div className="section-heading">
          <div>
            <span className="section-label">
              2026 DEMAND OUTLOOK
            </span>

            <h2 id="daily-forecast-heading">
              Daily ridership forecast
            </h2>
          </div>

          <span className="monitoring-period">
            {demandForecast?.model || "XGBoost"}
            {demandForecast?.model_version
              ? ` · ${demandForecast.model_version}`
              : ""}
          </span>
        </div>

        <div
          className="demand-forecast-panel"
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(190px, 1fr))",
            gap: "16px",
            padding: "22px",
            border: "1px solid var(--border-color, #dbe3ee)",
            borderRadius: "16px",
            background:
              "linear-gradient(135deg, #17263b, #0d1727)",
            color: "#f1f7ff",
          }}
        >
          <label
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            <span className="stat-label">
              Forecast target date
            </span>

            <input
              type="date"
              value={forecastDate}
              onChange={(event) =>
                setForecastDate(event.target.value)
              }
              aria-label="Forecast target date"
              style={{
                minHeight: "42px",
                padding: "8px 10px",
                borderRadius: "8px",
                border:
                  "1px solid var(--border-color, #cbd5e1)",
              }}
            />
          </label>

          <div>
            <span className="stat-label">
              Predicted daily ridership
            </span>

            <strong
              style={{
                display: "block",
                fontSize: "clamp(1.7rem, 3vw, 2.4rem)",
                marginTop: "8px",
              }}
            >
              {forecastLoading
                ? "Loading…"
                : formatNumber(
                    demandForecast?.forecast
                      ?.predicted_ridership
                  )}
            </strong>

            <span className="stat-description">
              Passengers · model-generated estimate
            </span>
          </div>

          <div>
            <span className="stat-label">
              Latest observed date
            </span>

            <strong
              style={{
                display: "block",
                marginTop: "8px",
              }}
            >
              {demandForecast?.latest_observed_date || "—"}
            </strong>

            <span className="stat-description">
              Latest recorded ridership:{" "}
              {formatNumber(
                demandForecast?.latest_observed_ridership
              )}
            </span>
          </div>

          <div>
            <span className="stat-label">
              Forecast horizon
            </span>

            <strong
              style={{
                display: "block",
                marginTop: "8px",
              }}
            >
              {demandForecast
                ?.days_ahead_from_latest_observation != null
                ? `${demandForecast.days_ahead_from_latest_observation} days`
                : "—"}
            </strong>

            <span className="stat-description">
              {demandForecast?.forecast_method ===
              "recursive_multi_day_forecast"
                ? "Recursive multi-day forecast"
                : demandForecast?.forecast_method ||
                  "Forecast method unavailable"}
            </span>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "end",
            }}
          >
            <button
              className="retry-button"
              type="button"
              onClick={() =>
                loadDemandForecast(forecastDate)
              }
              disabled={
                forecastLoading || !forecastDate
              }
            >
              {forecastLoading
                ? "Forecasting…"
                : "Update forecast"}
            </button>
          </div>
        </div>

        {forecastError && (
          <div
            className="monitoring-inline-error"
            role="alert"
            style={{ marginTop: "12px" }}
          >
            {forecastError}
          </div>
        )}
      </section>

      <section className="demand-section">
        <div className="section-heading">
          <div>
            <span className="section-label">
              NETWORK OVERVIEW
            </span>

            <h2>Station status</h2>
          </div>

          <span className="monitoring-period">
            {monitoring?.monitoring_date
              ? `${monitoring.monitoring_date} · ${String(
                  monitoring.monitoring_hour ?? ""
                ).padStart(2, "0")}:00`
              : "Waiting for update"}
          </span>
        </div>

        <div className="demand-stat-grid">
          <MetricCard
            label="Stations monitored"
            value={formatNumber(
              monitoring?.stations_monitored
            )}
          />

          <MetricCard
            label="Critical pressure"
            value={formatNumber(
              pressureLevels.CRITICAL || 0
            )}
            tone="severity-critical"
          />

          <MetricCard
            label="High pressure"
            value={formatNumber(
              pressureLevels.HIGH || 0
            )}
            tone="severity-high"
          />

          <MetricCard
            label="Moderate pressure"
            value={formatNumber(
              pressureLevels.MODERATE || 0
            )}
            tone="severity-moderate"
          />
        </div>
      </section>

      <section className="demand-section">
        <div className="section-heading">
          <div>
            <span className="section-label">
              HIGHEST DEMAND
            </span>

            <h2>
              {highest?.station || "Station overview"}
            </h2>
          </div>

          <span
            className={`priority-badge priority-${getPriorityClass(
              highest?.congestion_level
            )}`}
          >
            {highest?.congestion_level || "UNKNOWN"}
          </span>
        </div>

        <div className="highest-demand-card">
          <div className="highest-demand-main">
            <span className="station-label">
              Passenger entries (historical)
            </span>

            <div className="ridership-value">
              {formatNumber(highest?.current_ridership)}
            </div>

            <span className="ridership-label">
              Pressure score:{" "}
              {formatNumber(highest?.pressure_score, 2)}
            </span>
          </div>

          <div className="highest-demand-details">
            <div>
              <span>Passenger entries</span>
              <strong>
                {formatNumber(highest?.current_ridership)}
              </strong>
            </div>

            <div>
              <span>Passenger exits</span>
              <strong>
                {formatNumber(highest?.current_exit)}
              </strong>
            </div>

            <div>
              <span>Net passenger flow</span>
              <strong>
                {formatNumber(highest?.net_flow)}
              </strong>
            </div>

            <div>
              <span>Next-hour prediction</span>
              <strong>
                {formatNumber(
                  highest?.predicted_next_hour_ridership,
                  2
                )}
              </strong>
            </div>
          </div>
        </div>
      </section>

      <section className="demand-section">
        <div className="section-heading">
          <div>
            <span className="section-label">
              STATION EXPLORER
            </span>

            <h2>Station intelligence</h2>
          </div>

          <span className="monitoring-period">
            {stations.length} stations
          </span>
        </div>

        <div className="monitoring-toolbar">
          <input
            type="search"
            placeholder="Search station…"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            aria-label="Search station"
          />

          <select
            value={pressureFilter}
            onChange={(event) =>
              setPressureFilter(event.target.value)
            }
            aria-label="Filter by pressure"
          >
            <option value="ALL">All pressure levels</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MODERATE">Moderate</option>
            <option value="LOW">Low</option>
          </select>

          <select
            value={sortBy}
            onChange={(event) =>
              setSortBy(event.target.value)
            }
            aria-label="Sort stations"
          >
            <option value="pressure">Sort by risk</option>
            <option value="ridership">
              Sort by ridership
            </option>
            <option value="prediction">
              Sort by prediction
            </option>
            <option value="flow">Sort by net flow</option>
          </select>
        </div>

        <div className="station-card-grid">
          {visibleStations.map((station) => (
            <StationCard
              key={station.station}
              station={station}
              onView={setSelectedStation}
            />
          ))}
        </div>

        {stations.length === 0 && (
          <div className="monitoring-empty">
            No stations match these filters.
          </div>
        )}

        {stations.length > PAGE_SIZE && (
          <div className="station-pagination">
            <span>
              Showing {(page - 1) * PAGE_SIZE + 1}–
              {Math.min(
                page * PAGE_SIZE,
                stations.length
              )}{" "}
              of {stations.length}
            </span>

            <div>
              <button
                className="station-detail-button"
                type="button"
                disabled={page === 1}
                onClick={() =>
                  setPage((current) =>
                    Math.max(1, current - 1)
                  )
                }
              >
                ← Previous
              </button>

              <span className="station-page-number">
                {page} / {totalPages}
              </span>

              <button
                className="station-detail-button"
                type="button"
                disabled={page === totalPages}
                onClick={() =>
                  setPage((current) =>
                    Math.min(totalPages, current + 1)
                  )
                }
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </section>

      {stationDetails && (
        <div
          className="station-drawer-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setSelectedStation("");
            }
          }}
        >
          <aside
            className="station-drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="station-drawer-title"
          >
            <div className="station-drawer-header">
              <div>
                <span className="section-label">
                  STATION DETAILS
                </span>

                <h2 id="station-drawer-title">
                  {stationDetails.station}
                </h2>

                <span
                  className={`priority-badge priority-${getPriorityClass(
                    getSeverity(stationDetails)
                  )}`}
                >
                  {getSeverity(stationDetails)}
                </span>
              </div>

              <button
                className="station-drawer-close"
                type="button"
                aria-label="Close station details"
                onClick={() => setSelectedStation("")}
              >
                ✕
              </button>
            </div>

            <div className="station-drawer-body">
              <div className="station-drawer-pressure">
                <span>Pressure score</span>

                <strong>
                  {formatNumber(
                    stationDetails.pressure_score,
                    2
                  )}
                </strong>

                <div className="station-pressure-track">
                  <span
                    className={`station-pressure-fill pressure-fill-${getPriorityClass(
                      getSeverity(stationDetails)
                    )}`}
                    style={{
                      width: `${Math.max(
                        0,
                        Math.min(
                          100,
                          Number(
                            stationDetails.pressure_score
                          ) || 0
                        )
                      )}%`,
                    }}
                  />
                </div>
              </div>

              <div className="station-drawer-metrics">
                <MetricCard
                  label="Passenger entries"
                  value={formatNumber(
                    stationDetails.current_ridership
                  )}
                />

                <MetricCard
                  label="Passenger exits"
                  value={formatNumber(
                    stationDetails.current_exit
                  )}
                />

                <MetricCard
                  label="Net passenger flow"
                  value={formatNumber(
                    stationDetails.net_flow
                  )}
                />

                <MetricCard
                  label="Next-hour prediction"
                  value={formatNumber(
                    stationDetails.predicted_next_hour_ridership,
                    2
                  )}
                />
              </div>

              <div className="station-related-alerts">
                <h3>Related alerts</h3>

                {relatedAlerts.length === 0 ? (
                  <p>
                    No high-pressure alerts for this
                    station right now.
                  </p>
                ) : (
                  relatedAlerts.map((alert, index) => (
                    <AlertCard
                      key={`${alert.station}-${alert.alert_type}-${index}`}
                      alert={alert}
                      index={index}
                    />
                  ))
                )}
              </div>
            </div>
          </aside>
        </div>
      )}

      <section className="demand-section">
        <div className="section-heading">
          <div>
            <span className="section-label">
              ALERT CENTER
            </span>

            <h2>Historical pressure alerts</h2>
          </div>

          <span className="monitoring-period">
            {alerts.length} active alerts
          </span>
        </div>

        <div className="alert-grid">
          {["CRITICAL", "HIGH", "MODERATE", "LOW"].map(
            (severity) => (
              <article
                className={`alert-card alert-${severity.toLowerCase()}`}
                key={severity}
              >
                <span>{severity}</span>

                <strong>
                  {formatNumber(
                    severityCounts[severity] || 0
                  )}
                </strong>
              </article>
            )
          )}
        </div>

        <div className="monitoring-alert-list">
          {visibleAlerts.map((alert, index) => (
            <AlertCard
              key={`${alert.station}-${alert.alert_type}-${index}`}
              alert={alert}
              index={index}
            />
          ))}

          {alerts.length === 0 && (
            <div className="monitoring-empty">
              No stations in this snapshot meet the
              high-pressure alert threshold.
            </div>
          )}
        </div>

        {alerts.length > INITIAL_ALERTS && (
          <button
            className="alerts-toggle-button"
            type="button"
            onClick={() =>
              setShowAllAlerts((value) => !value)
            }
          >
            {showAllAlerts
              ? "Show fewer alerts ↑"
              : `View all ${alerts.length} alerts ↓`}
          </button>
        )}
      </section>

      <footer className="monitoring-last-updated">
        <span>
          {refreshing
            ? "Updating network…"
            : "Network monitoring"}
        </span>

        <span>
          {lastUpdated
            ? `Last update ${lastUpdated.toLocaleTimeString()}`
            : "Waiting for first update"}
        </span>
      </footer>
    </main>
  );
}