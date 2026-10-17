import React, { useEffect, useMemo, useState } from "react";
import "../styles/Analytics.css";

import api, {
  getAnalyticsOverview,
  getAnalyticsTrends,
  getAnalyticsAnomalies,
  getAnalyticsStations,
  getAnalyticsPassengerFlow,
  getAnalyticsHotspots,
  getAnalyticsModelInsights,
  getAnalyticsHeatmap,
} from "../services/api";

const HOURS = Array.from({ length: 24 }, (_, index) => index);
const MONITORING_INTERVAL = 15000;
const MAX_MONITORING_POINTS = 2000;

const EMPTY_DATA = {
  overview: null,
  trends: null,
  anomalies: null,
  stations: null,
  passengerFlow: null,
  hotspots: null,
  modelInsights: null,
  heatmap: null,
};

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "—";

  const number = Number(value);

  return Number.isFinite(number)
    ? Math.round(number).toLocaleString("en-IN")
    : "—";
}

function formatDecimal(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "—";

  const number = Number(value);

  return Number.isFinite(number) ? number.toFixed(digits) : "—";
}

function getFirst(object, keys, fallback = null) {
  if (!object || typeof object !== "object") return fallback;

  for (const key of keys) {
    if (object[key] !== undefined && object[key] !== null) {
      return object[key];
    }
  }

  return fallback;
}

function getArray(payload, keys = []) {
  if (Array.isArray(payload)) return payload;

  for (const key of keys) {
    if (Array.isArray(payload?.[key])) return payload[key];
  }

  return [];
}

function readNumber(row, keys) {
  const value = getFirst(row, keys);

  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number) ? number : null;
}

function readStation(row) {
  return String(
    getFirst(
      row,
      ["station", "Station", "name", "station_name"],
      "Unknown station"
    )
  );
}

function titleCase(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getPressureLevel(station) {
  const suppliedLevel = String(
    getFirst(
      station,
      ["congestion_level", "pressure_level", "risk_level"],
      ""
    )
  )
    .trim()
    .toUpperCase();

  if (
    suppliedLevel === "UNAVAILABLE" ||
    station?.data_available === false
  ) {
    return "UNAVAILABLE";
  }

  if (
    ["LOW", "MODERATE", "HIGH", "CRITICAL"].includes(suppliedLevel)
  ) {
    return suppliedLevel;
  }

  const score = readNumber(station, ["pressure_score", "pressure"]);

  if (score === null) return "UNKNOWN";
  if (score >= 85) return "CRITICAL";
  if (score >= 60) return "HIGH";
  if (score >= 30) return "MODERATE";

  return "LOW";
}

function pressureClass(level) {
  return String(level).toLowerCase().replace(/[^a-z-]/g, "");
}

function isSnapshotUnavailable(snapshot) {
  return (
    snapshot?.data_available === false ||
    getPressureLevel(snapshot) === "UNAVAILABLE"
  );
}

function getSnapshotEntries(snapshot) {
  if (isSnapshotUnavailable(snapshot)) return 0;

  return (
    readNumber(snapshot, [
      "current_ridership",
      "observed_entries",
      "entries",
      "entry",
    ]) ?? 0
  );
}

function getSnapshotExits(snapshot) {
  if (isSnapshotUnavailable(snapshot)) return 0;

  return (
    readNumber(snapshot, [
      "current_exit",
      "observed_exits",
      "exits",
      "exit",
    ]) ?? 0
  );
}

function getSnapshotPrediction(snapshot) {
  if (isSnapshotUnavailable(snapshot)) return null;

  const value =
    snapshot?.ml_predicted_next_hour_ridership ??
    snapshot?.predicted_next_hour_ridership ??
    snapshot?.predicted_ridership ??
    snapshot?.predicted_demand ??
    snapshot?.prediction;

  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number) ? number : null;
}

function getPredictionStatus(snapshot) {
  if (isSnapshotUnavailable(snapshot)) {
    return "Station observation unavailable";
  }

  if (getSnapshotPrediction(snapshot) === null) {
    return "Prediction unavailable";
  }

  return "Prediction available";
}

function renderPrediction(snapshot) {
  const status = getPredictionStatus(snapshot);

  if (status === "Station observation unavailable") {
    return (
      <span
        className="analytics-prediction-unavailable"
        title="No station observation is available for this timestamp."
      >
        Observation unavailable
      </span>
    );
  }

  if (status === "Prediction unavailable") {
    return (
      <span
        className="analytics-prediction-unavailable"
        title="The required model input features are not available for this observation."
      >
        —
      </span>
    );
  }

  return formatNumber(getSnapshotPrediction(snapshot));
}

function getSnapshotNetFlow(snapshot) {
  if (isSnapshotUnavailable(snapshot)) return null;

  const supplied = readNumber(snapshot, [
    "net_flow",
    "Net_Flow",
    "Net Flow",
    "net",
  ]);

  return supplied ?? getSnapshotEntries(snapshot) - getSnapshotExits(snapshot);
}

function displaySnapshotValue(snapshot, getter) {
  return isSnapshotUnavailable(snapshot)
    ? "—"
    : formatNumber(getter(snapshot));
}

function formatTimestamp(value) {
  if (!value) return "Waiting for first update";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function getMonitoringHour(monitoring) {
  const value = monitoring?.monitoring_hour ?? monitoring?.hour;

  return value == null ? null : Number(value);
}

function SectionHeading({ eyebrow, title, description, right }) {
  return (
    <div className="analytics-section-heading">
      <div>
        {eyebrow && <p className="analytics-eyebrow">{eyebrow}</p>}

        <h2>{title}</h2>

        {description && (
          <p className="analytics-section-description">{description}</p>
        )}
      </div>

      {right && <div className="analytics-heading-action">{right}</div>}
    </div>
  );
}

function MetricCard({ label, value, detail }) {
  return (
    <article className="analytics-metric-card">
      <p className="analytics-metric-label">{label}</p>
      <div className="analytics-metric-value">{value}</div>

      {detail && <p className="analytics-metric-detail">{detail}</p>}
    </article>
  );
}

function EmptyState({
  message = "No data is available for this section.",
}) {
  return <div className="analytics-empty-state">{message}</div>;
}

function LoadingState() {
  return (
    <div className="analytics-loading">
      <span className="analytics-spinner" />
      <span>Loading analytics…</span>
    </div>
  );
}

function ErrorMessage({ message }) {
  if (!message) return null;

  return (
    <div className="analytics-error" role="alert">
      {message}
    </div>
  );
}

function DataTable({ columns, rows, emptyMessage }) {
  if (!rows.length) return <EmptyState message={emptyMessage} />;

  return (
    <div className="analytics-table-wrap">
      <table className="analytics-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.map((row, index) => (
            <tr key={row.id ?? row.station ?? row.Station ?? index}>
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render
                    ? column.render(row[column.key], row)
                    : String(row[column.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TrendChart({ rows }) {
  if (!rows.length) {
    return <EmptyState message="Waiting for trend data." />;
  }

  const visibleRows = rows.slice(-30);

  const maxValue = Math.max(
    ...visibleRows.map((row) => Number(row.value) || 0),
    1
  );

  return (
    <div className="analytics-trend-chart">
      {visibleRows.map((row, index) => {
        const value = Number(row.value) || 0;
        const height = Math.max((value / maxValue) * 100, 2);

        return (
          <div
            className="analytics-trend-column"
            key={`${row.timestamp}-${index}`}
          >
            <div className="analytics-trend-value">
              {formatNumber(value)}
            </div>

            <div className="analytics-trend-bar-area">
              <div
                className="analytics-trend-bar"
                style={{ height: `${height}%` }}
                title={`${row.label}: ${formatNumber(value)}`}
              />
            </div>

            <div className="analytics-trend-label" title={row.label}>
              {row.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function MonitoringDistribution({ counts, total }) {
  const levels = [
    { key: "CRITICAL", label: "Critical" },
    { key: "HIGH", label: "High" },
    { key: "MODERATE", label: "Moderate" },
    { key: "LOW", label: "Low" },
    { key: "UNKNOWN", label: "Unclassified" },
    { key: "UNAVAILABLE", label: "Unavailable" },
  ];

  return (
    <div className="analytics-monitoring-distribution">
      {levels.map((level) => {
        const count = counts[level.key] ?? 0;
        const percentage = total > 0 ? (count / total) * 100 : 0;

        return (
          <div className="analytics-pressure-row" key={level.key}>
            <div className="analytics-pressure-row-heading">
              <span
                className={`analytics-pressure-label pressure-${pressureClass(
                  level.key
                )}`}
              >
                {level.label}
              </span>

              <strong>
                {formatNumber(count)}{" "}
                <span className="analytics-pressure-percent">
                  ({formatDecimal(percentage, 1)}%)
                </span>
              </strong>
            </div>

            <div
              className="analytics-pressure-track"
              role="img"
              aria-label={`${level.label}: ${count} of ${total} stations`}
            >
              <div
                className={`analytics-pressure-fill pressure-${pressureClass(
                  level.key
                )}`}
                style={{ width: `${Math.min(percentage, 100)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Heatmap({ rows, valueLabel = "average entries" }) {
  if (!rows.length) {
    return <EmptyState message="Station-hour data is unavailable." />;
  }

  const maxValue = Math.max(
    1,
    ...rows.flatMap((station) => station.values)
  );

  return (
    <div className="analytics-heatmap-content">
      <div className="analytics-heatmap-legend">
        <span>Lower {valueLabel}</span>

        <div className="analytics-legend-scale" aria-hidden="true">
          {[1, 2, 3, 4, 5].map((step) => (
            <span
              key={step}
              className={`analytics-legend-step step-${step}`}
            />
          ))}
        </div>

        <span>Higher {valueLabel}</span>
      </div>

      <div className="analytics-heatmap-scroll">
        <table className="analytics-heatmap-table">
          <thead>
            <tr>
              <th className="analytics-heatmap-station-header" scope="col">
                Station
              </th>

              {HOURS.map((hour) => (
                <th key={hour} scope="col">
                  {String(hour).padStart(2, "0")}
                </th>
              ))}

              <th className="analytics-heatmap-total-header" scope="col">
                Total
              </th>
            </tr>
          </thead>

          <tbody>
            {rows.map((station) => (
              <tr key={station.station}>
                <th className="analytics-heatmap-station" scope="row">
                  {station.station}
                </th>

                {HOURS.map((hour) => {
                  const value = Number(station.values[hour] ?? 0);
                  const intensity = Math.min(
                    1,
                    Math.max(0, value) / maxValue
                  );
                  const alpha =
                    value > 0 ? 0.18 + intensity * 0.82 : 0.04;

                  return (
                    <td
                      className="analytics-heatmap-cell-wrapper"
                      key={hour}
                    >
                      <div
                        className="analytics-heatmap-cell"
                        style={{
                          backgroundColor: `rgba(34, 197, 154, ${alpha})`,
                          color:
                            intensity > 0.45 ? "#04130f" : "#e5fff6",
                        }}
                        title={`${station.station}, ${String(hour).padStart(
                          2,
                          "0"
                        )}:00 — ${valueLabel}: ${formatNumber(value)}`}
                        aria-label={`${station.station}, ${String(
                          hour
                        ).padStart(2, "0")}:00, ${valueLabel}: ${formatNumber(
                          value
                        )}`}
                        tabIndex={0}
                      >
                        {value > 0 ? formatNumber(value) : "·"}
                      </div>
                    </td>
                  );
                })}

                <td className="analytics-heatmap-total">
                  {formatNumber(
                    station.values.reduce(
                      (sum, value) => sum + (Number(value) || 0),
                      0
                    )
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RecommendationCard({ recommendation }) {
  return (
    <article className="analytics-recommendation-card">
      <div className="analytics-recommendation-topline">
        <span
          className={`analytics-recommendation-priority priority-${recommendation.priority.toLowerCase()}`}
        >
          {recommendation.priority}
        </span>

        {recommendation.station && (
          <span className="analytics-recommendation-station">
            {recommendation.station}
          </span>
        )}
      </div>

      <h3>{recommendation.title}</h3>

      <div className="analytics-recommendation-block">
        <span>Evidence</span>
        <p>{recommendation.evidence}</p>
      </div>

      <div className="analytics-recommendation-block">
        <span>Suggested follow-up</span>
        <p>{recommendation.action}</p>
      </div>
    </article>
  );
}

function buildRecommendations({ hotspots, flow, trends, anomalies }) {
  const recommendations = [];

  const availableHotspots = hotspots.filter(
    (station) => !isSnapshotUnavailable(station)
  );

  const availableFlow = flow.filter(
    (station) =>
      !isSnapshotUnavailable(station) &&
      getSnapshotNetFlow(station) !== null
  );

  if (availableHotspots.length) {
    const top = availableHotspots[0];

    recommendations.push({
      id: "top-station",
      priority: "Review",
      title: "Review the highest-entry station",
      station: readStation(top),
      evidence: `${formatNumber(
        getSnapshotEntries(top)
      )} entries in the latest monitoring snapshot.`,
      action:
        "Compare entries and predicted demand across subsequent observations.",
    });
  }

  if (availableFlow.length) {
    const largestFlow = [...availableFlow].sort(
      (a, b) => getSnapshotNetFlow(b) - getSnapshotNetFlow(a)
    )[0];

    recommendations.push({
      id: "net-flow",
      priority: "Insight",
      title: "Review the highest positive net flow",
      station: readStation(largestFlow),
      evidence: `Net flow: ${formatNumber(
        getSnapshotNetFlow(largestFlow)
      )}.`,
      action:
        "Compare entries and exits over subsequent observations to see whether the pattern continues.",
    });
  }

  if (trends.length >= 2) {
    const previous = trends[trends.length - 2];
    const latest = trends[trends.length - 1];
    const difference = latest.value - previous.value;

    recommendations.push({
      id: "trend-change",
      priority: "Review",
      title:
        difference > 0
          ? "Network entries increased in the latest observation"
          : difference < 0
            ? "Network entries decreased in the latest observation"
            : "Network entries remained stable",
      evidence: `${previous.label}: ${formatNumber(
        previous.value
      )}; ${latest.label}: ${formatNumber(latest.value)}.`,
      action:
        "Review station-level values and subsequent observations before drawing conclusions from one change.",
    });
  }

  if (anomalies.length) {
    recommendations.push({
      id: "anomalies",
      priority: "Review",
      title: "Review statistically flagged observations",
      evidence: `${formatNumber(
        anomalies.length
      )} records were returned by the anomaly analysis.`,
      action:
        "Inspect flagged records and neighboring observations to assess whether the pattern persists.",
    });
  }

  return recommendations;
}

function buildHistoricalHeatmap(payload) {
  const stations = getArray(payload, ["heatmap", "data", "rows"]);

  return stations
    .map((row) => {
      const rawValues = Array.isArray(row.hourly_ridership)
        ? row.hourly_ridership
        : Array.isArray(row.values)
          ? row.values
          : [];

      return {
        station: readStation(row),
        values: HOURS.map((hour) => {
          const value = Number(rawValues[hour] ?? 0);

          return Number.isFinite(value) ? value : 0;
        }),
        total: readNumber(row, ["total_ridership", "total"]) ?? 0,
      };
    })
    .filter((row) => row.station !== "Unknown station")
    .sort((a, b) => a.station.localeCompare(b.station));
}

export default function Analytics() {
  const [data, setData] = useState(EMPTY_DATA);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});

  const [monitoring, setMonitoring] = useState(null);
  const [monitoringError, setMonitoringError] = useState("");
  const [monitoringLoading, setMonitoringLoading] = useState(true);
  const [monitoringSearch, setMonitoringSearch] = useState("");
  const [monitoringFilter, setMonitoringFilter] = useState("ALL");
  const [monitoringHistory, setMonitoringHistory] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadAnalytics() {
      setLoading(true);

      const requests = [
        ["overview", getAnalyticsOverview],
        ["trends", getAnalyticsTrends],
        ["anomalies", getAnalyticsAnomalies],
        ["stations", getAnalyticsStations],
        ["passengerFlow", getAnalyticsPassengerFlow],
        ["hotspots", getAnalyticsHotspots],
        ["modelInsights", getAnalyticsModelInsights],
        ["heatmap", getAnalyticsHeatmap],
      ];

      const results = await Promise.allSettled(
        requests.map(([, request]) => request())
      );

      if (cancelled) return;

      const nextData = { ...EMPTY_DATA };
      const nextErrors = {};

      results.forEach((result, index) => {
        const key = requests[index][0];

        if (result.status === "fulfilled") {
          nextData[key] = result.value;
        } else {
          nextErrors[key] =
            result.reason?.response?.data?.detail ||
            result.reason?.message ||
            "Unable to load this analytics section.";
        }
      });

      setData(nextData);
      setErrors(nextErrors);
      setLoading(false);
    }

    loadAnalytics();

    return () => {
      cancelled = true;
    };
  }, []);

  // Refresh the monitoring snapshot every 15 seconds.
  useEffect(() => {
    let cancelled = false;
    let timeoutId;

    async function loadMonitoringSnapshot() {
      try {
        const response = await api.get("/monitoring/replay/next");

        if (cancelled) return;

        const payload = response.data;

        if (!Array.isArray(payload?.station_snapshots)) {
          throw new Error(
            "The monitoring endpoint did not return station snapshots."
          );
        }

        const sourceTimestamp =
          payload.observation_timestamp ||
          payload.source_observation_timestamp ||
          payload.monitoring_timestamp ||
          `${payload.monitoring_date ?? payload.date ?? ""}T${String(
            payload.monitoring_hour ?? payload.hour ?? 0
          ).padStart(2, "0")}:00:00`;

        const historyPoint = {
          timestamp: sourceTimestamp,
          station_snapshots: payload.station_snapshots,
        };

        setMonitoring(payload);
        setLastUpdated(new Date().toISOString());
        setMonitoringError("");

        setMonitoringHistory((previous) => {
          const alreadyStored = previous.some(
            (point) => point.timestamp === historyPoint.timestamp
          );

          if (alreadyStored) return previous;

          return [...previous, historyPoint].slice(-MAX_MONITORING_POINTS);
        });
      } catch (error) {
        if (!cancelled) {
          setMonitoringError(
            error?.response?.data?.detail ||
              error?.message ||
              "Unable to retrieve the monitoring snapshot."
          );
        }
      } finally {
        if (!cancelled) {
          setMonitoringLoading(false);
          timeoutId = window.setTimeout(
            loadMonitoringSnapshot,
            MONITORING_INTERVAL
          );
        }
      }
    }

    setMonitoringLoading(true);
    loadMonitoringSnapshot();

    return () => {
      cancelled = true;

      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, []);

  const overview = data.overview ?? {};
  const modelInsights = data.modelInsights ?? {};
  const monitoringStations = monitoring?.station_snapshots ?? [];

  const monitoringCounts = useMemo(() => {
    const counts = {
      LOW: 0,
      MODERATE: 0,
      HIGH: 0,
      CRITICAL: 0,
      UNKNOWN: 0,
      UNAVAILABLE: 0,
    };

    monitoringStations.forEach((station) => {
      const level = getPressureLevel(station);
      counts[level] = (counts[level] ?? 0) + 1;
    });

    return counts;
  }, [monitoringStations]);

  const monitoringVisibleStations = useMemo(() => {
    const search = monitoringSearch.trim().toLowerCase();

    const order = {
      CRITICAL: 0,
      HIGH: 1,
      MODERATE: 2,
      LOW: 3,
      UNKNOWN: 4,
      UNAVAILABLE: 5,
    };

    return [...monitoringStations]
      .filter((station) => {
        const matchesSearch = readStation(station)
          .toLowerCase()
          .includes(search);

        const level = getPressureLevel(station);

        return (
          matchesSearch &&
          (monitoringFilter === "ALL" || level === monitoringFilter)
        );
      })
      .sort((a, b) => {
        const difference =
          order[getPressureLevel(a)] - order[getPressureLevel(b)];

        if (difference !== 0) return difference;

        return (
          (readNumber(b, ["pressure_score", "pressure"]) ?? -1) -
          (readNumber(a, ["pressure_score", "pressure"]) ?? -1)
        );
      });
  }, [monitoringStations, monitoringSearch, monitoringFilter]);

  const monitoringTrends = useMemo(
    () =>
      monitoringHistory.map((point) => ({
        timestamp: point.timestamp,
        label: formatTimestamp(point.timestamp),
        value: point.station_snapshots.reduce(
          (sum, station) => sum + getSnapshotEntries(station),
          0
        ),
      })),
    [monitoringHistory]
  );

  const monitoringComparisonStations = useMemo(() => {
    const averages = new Map();

    monitoringHistory.forEach((point) => {
      point.station_snapshots.forEach((station) => {
        if (isSnapshotUnavailable(station)) return;

        const name = readStation(station);
        const current = averages.get(name) ?? { total: 0, count: 0 };

        current.total += getSnapshotEntries(station);
        current.count += 1;

        averages.set(name, current);
      });
    });

    return monitoringStations.map((station) => {
      const name = readStation(station);
      const aggregate = averages.get(name);
      const unavailable = isSnapshotUnavailable(station);

      return {
        ...station,
        station: name,
        Station: name,
        Ridership: unavailable ? null : getSnapshotEntries(station),
        Average: unavailable
          ? null
          : aggregate?.count
            ? aggregate.total / aggregate.count
            : getSnapshotEntries(station),
      };
    });
  }, [monitoringStations, monitoringHistory]);

  const monitoringHotspots = useMemo(
    () =>
      [...monitoringComparisonStations]
        .filter((station) => !isSnapshotUnavailable(station))
        .sort(
          (a, b) => getSnapshotEntries(b) - getSnapshotEntries(a)
        ),
    [monitoringComparisonStations]
  );

  const monitoringFlow = useMemo(
    () =>
      monitoringComparisonStations.map((station) => ({
        ...station,
        entries: getSnapshotEntries(station),
        exits: getSnapshotExits(station),
        net_flow: getSnapshotNetFlow(station),
      })),
    [monitoringComparisonStations]
  );

  const stationHourHeatmap = useMemo(
    () => buildHistoricalHeatmap(data.heatmap),
    [data.heatmap]
  );

  const anomalies = getArray(data.anomalies, [
    "anomalies",
    "outliers",
    "data",
    "rows",
  ]);

  const recommendations = useMemo(
    () =>
      buildRecommendations({
        hotspots: monitoringHotspots,
        flow: monitoringFlow,
        trends: monitoringTrends,
        anomalies,
      }),
    [monitoringHotspots, monitoringFlow, monitoringTrends, anomalies]
  );

  const overviewMetrics = [
    {
      label: "Stations covered",
      value: formatNumber(
        getFirst(overview, [
          "stations_covered",
          "station_count",
          "total_stations",
        ])
      ),
      detail: "Stations in the dataset",
    },
    {
      label: "Recorded observations",
      value: formatNumber(
        getFirst(overview, [
          "observation_rows",
          "total_records",
          "record_count",
          "observations",
        ])
      ),
      detail: "Available station-hour records",
    },
    {
      label: "Total recorded ridership",
      value: formatNumber(
        getFirst(overview, [
          "total_recorded_ridership",
          "total_ridership",
          "ridership_total",
          "total_passengers",
        ])
      ),
      detail: "Across the available dataset",
    },
    {
      label: "Date coverage",
      value:
        getFirst(overview, ["date_range", "period", "coverage"]) ??
        ([
          getFirst(overview, ["start_date", "first_date"]),
          getFirst(overview, ["end_date", "last_date"]),
        ]
          .filter(Boolean)
          .join(" – ") ||
          "—"),
      detail: "Available data period",
    },
  ];

  const stationColumns = [
    {
      key: "station",
      label: "Station",
      render: (_, row) => readStation(row),
    },
    {
      key: "Ridership",
      label: "Current entries",
      render: (_, row) =>
        displaySnapshotValue(row, getSnapshotEntries),
    },
    {
      key: "Average",
      label: "Average entries",
      render: (_, row) =>
        isSnapshotUnavailable(row) ? "—" : formatNumber(row.Average),
    },
    {
      key: "predicted",
      label: "Predicted demand",
      render: (_, row) => renderPrediction(row),
    },
  ];

  const hotspotColumns = [
    {
      key: "station",
      label: "Station",
      render: (_, row) => readStation(row),
    },
    {
      key: "entries",
      label: "Current entries",
      render: (_, row) =>
        displaySnapshotValue(row, getSnapshotEntries),
    },
    {
      key: "pressure",
      label: "Pressure",
      render: (_, row) => (
        <span
          className={`analytics-pressure-label pressure-${pressureClass(
            getPressureLevel(row)
          )}`}
        >
          {titleCase(getPressureLevel(row))}
        </span>
      ),
    },
    {
      key: "hour",
      label: "Monitoring hour",
      render: () => {
        const hour = getMonitoringHour(monitoring);

        return hour == null
          ? "—"
          : `${String(hour).padStart(2, "0")}:00`;
      },
    },
  ];

  const flowColumns = [
    {
      key: "station",
      label: "Station",
      render: (_, row) => readStation(row),
    },
    {
      key: "entries",
      label: "Entries",
      render: (_, row) =>
        displaySnapshotValue(row, getSnapshotEntries),
    },
    {
      key: "exits",
      label: "Exits",
      render: (_, row) =>
        displaySnapshotValue(row, getSnapshotExits),
    },
    {
      key: "net_flow",
      label: "Net flow",
      render: (_, row) =>
        isSnapshotUnavailable(row)
          ? "—"
          : formatNumber(getSnapshotNetFlow(row)),
    },
  ];

  const monitoringColumns = [
    {
      key: "station",
      label: "Station",
      render: (_, row) => readStation(row),
    },
    {
      key: "pressure",
      label: "Pressure",
      render: (_, row) => (
        <span
          className={`analytics-pressure-label pressure-${pressureClass(
            getPressureLevel(row)
          )}`}
        >
          {titleCase(getPressureLevel(row))}
        </span>
      ),
    },
    {
      key: "score",
      label: "Pressure score",
      render: (_, row) =>
        isSnapshotUnavailable(row)
          ? "—"
          : formatDecimal(
              readNumber(row, ["pressure_score", "pressure"])
            ),
    },
    {
      key: "entries",
      label: "Entries",
      render: (_, row) =>
        displaySnapshotValue(row, getSnapshotEntries),
    },
    {
      key: "exits",
      label: "Exits",
      render: (_, row) =>
        displaySnapshotValue(row, getSnapshotExits),
    },
    {
      key: "flow",
      label: "Net flow",
      render: (_, row) =>
        isSnapshotUnavailable(row)
          ? "—"
          : formatNumber(getSnapshotNetFlow(row)),
    },
    {
      key: "prediction",
      label: "Predicted demand",
      render: (_, row) => renderPrediction(row),
    },
  ];

  const modelMetrics = [
    {
      label: "Model",
      value: getFirst(
        modelInsights,
        ["available_prediction_model", "model_name", "model", "name"],
        "XGBoost"
      ),
    },
    {
      label: "MAE",
      value:
        modelInsights.evaluation_metrics?.mae ??
        getFirst(modelInsights, ["mae", "test_mae"]),
    },
    {
      label: "RMSE",
      value:
        modelInsights.evaluation_metrics?.rmse ??
        getFirst(modelInsights, ["rmse", "test_rmse"]),
    },
    {
      label: "R² score",
      value:
        modelInsights.evaluation_metrics?.r_squared ??
        getFirst(modelInsights, ["r2", "r2_score", "test_r2"]),
    },
  ];

  const networkEntries = monitoringStations.reduce(
    (sum, station) => sum + getSnapshotEntries(station),
    0
  );

  const networkExits = monitoringStations.reduce(
    (sum, station) => sum + getSnapshotExits(station),
    0
  );

  const availablePressureStations = monitoringStations.filter(
    (station) =>
      !isSnapshotUnavailable(station) &&
      readNumber(station, ["pressure_score", "pressure"]) !== null
  );

  const averagePressure = availablePressureStations.length
    ? availablePressureStations.reduce(
        (sum, station) =>
          sum + readNumber(station, ["pressure_score", "pressure"]),
        0
      ) / availablePressureStations.length
    : null;

  const availablePredictions = monitoringStations
    .filter((station) => !isSnapshotUnavailable(station))
    .map(getSnapshotPrediction)
    .filter((value) => value !== null);

  const predictedNetworkDemand = availablePredictions.length
    ? availablePredictions.reduce((sum, value) => sum + value, 0)
    : null;

  return (
    <main className="analytics-page">
      <header className="analytics-page-header">
        <div>
          <p className="analytics-eyebrow">
            AI METROFLOW · NETWORK INTELLIGENCE
          </p>

          <h1>Live Monitoring and Analytics</h1>

          <p className="analytics-page-subtitle">
            Monitor station activity, passenger movement, demand predictions,
            network patterns, and machine-learning insights.
          </p>

          <p className="analytics-source-note">
            Last updated: {formatTimestamp(lastUpdated)}
          </p>
        </div>

        <div className="analytics-source-pill">
          <span className="analytics-source-dot" />
          {monitoringError
            ? "Connection Issue"
            : monitoringLoading
              ? "Connecting"
              : "Monitoring Active"}
        </div>
      </header>

      {loading && !data.overview && <LoadingState />}

      <section className="analytics-section" id="overview">
        <SectionHeading
          eyebrow="01 · NETWORK"
          title="Network Overview"
          description="Dataset coverage and current network monitoring readings."
        />

        <ErrorMessage message={errors.overview} />

        <div className="analytics-metric-grid">
          {overviewMetrics.map((metric) => (
            <MetricCard key={metric.label} {...metric} />
          ))}
        </div>

        <div className="analytics-metric-grid">
          <MetricCard
            label="Current network entries"
            value={formatNumber(networkEntries)}
            detail="Sum of entries in the current snapshot"
          />

          <MetricCard
            label="Current network exits"
            value={formatNumber(networkExits)}
            detail="Sum of exits in the current snapshot"
          />

          <MetricCard
            label="Predicted network demand"
            value={formatNumber(predictedNetworkDemand)}
            detail={`${availablePredictions.length} station-level predictions available`}
          />

          <MetricCard
            label="Average pressure score"
            value={
              averagePressure === null
                ? "—"
                : formatDecimal(averagePressure)
            }
            detail={`${availablePressureStations.length} stations with available pressure scores`}
          />
        </div>
      </section>

      <section
        className="analytics-section"
        id="operational-monitoring"
      >
        <SectionHeading
          eyebrow="02 · STATION MONITORING"
          title="Station Pressure Overview"
          description="Station activity, analytical pressure levels, and model-estimated next-hour demand."
          right={
            <a
              className="analytics-monitoring-link"
              href="/crowd-monitoring"
            >
              Open Crowd Monitoring <span aria-hidden="true">→</span>
            </a>
          }
        />

        {monitoringLoading && !monitoring && <LoadingState />}
        <ErrorMessage message={monitoringError} />

        {monitoring && (
          <>
            <div className="analytics-metric-grid">
              <MetricCard
                label="Stations monitored"
                value={formatNumber(monitoringStations.length)}
                detail="Stations in the current monitoring snapshot"
              />

              <MetricCard
                label="Critical pressure"
                value={formatNumber(monitoringCounts.CRITICAL)}
                detail="Current critical classification"
              />

              <MetricCard
                label="High pressure"
                value={formatNumber(monitoringCounts.HIGH)}
                detail="Current high classification"
              />

              <MetricCard
                label="Moderate pressure"
                value={formatNumber(monitoringCounts.MODERATE)}
                detail="Current moderate classification"
              />
            </div>

            <div className="analytics-monitoring-panel">
              <SectionHeading
                eyebrow="PRESSURE DISTRIBUTION"
                title="Network Pressure Levels"
                description="Distribution of station pressure classifications, including stations without an observation."
              />

              <MonitoringDistribution
                counts={monitoringCounts}
                total={monitoringStations.length}
              />
            </div>

            <div className="analytics-monitoring-panel">
              <SectionHeading
                eyebrow="STATION DETAILS"
                title="Station Monitoring Records"
                description="Station readings, analytical pressure scores, and model predictions."
                right={
                  <span className="analytics-data-tag">
                    {formatNumber(monitoringVisibleStations.length)} shown
                  </span>
                }
              />

              <div className="analytics-monitoring-toolbar">
                <label className="analytics-filter-field">
                  <span>Search station</span>

                  <input
                    type="search"
                    value={monitoringSearch}
                    onChange={(event) =>
                      setMonitoringSearch(event.target.value)
                    }
                    placeholder="Enter station name…"
                  />
                </label>

                <label className="analytics-filter-field">
                  <span>Pressure level</span>

                  <select
                    value={monitoringFilter}
                    onChange={(event) =>
                      setMonitoringFilter(event.target.value)
                    }
                  >
                    <option value="ALL">All levels</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="LOW">Low</option>
                    <option value="UNKNOWN">Unclassified</option>
                    <option value="UNAVAILABLE">Unavailable</option>
                  </select>
                </label>
              </div>

              <DataTable
                columns={monitoringColumns}
                rows={monitoringVisibleStations}
                emptyMessage="No stations match your filters."
              />

              <p className="analytics-section-description">
                Predicted demand is displayed when the required model inputs
                are available. Missing predictions are not treated as zero.
              </p>
            </div>
          </>
        )}
      </section>

      <section className="analytics-section" id="trends">
        <SectionHeading
          eyebrow="03 · TIME SERIES"
          title="Ridership Trends"
          description="Network entries across the monitoring observations received."
          right={
            <span className="analytics-data-tag">
              {monitoringHistory.length} observations
            </span>
          }
        />

        <TrendChart rows={monitoringTrends} />
      </section>

      <section className="analytics-section" id="stations">
        <SectionHeading
          eyebrow="04 · STATION ANALYSIS"
          title="Station Comparison"
          description="Current entries, average observed activity, and predicted demand."
        />

        <DataTable
          columns={stationColumns}
          rows={monitoringComparisonStations}
          emptyMessage="Station comparison will appear after the first observation."
        />
      </section>

      <section className="analytics-section" id="hotspots">
        <SectionHeading
          eyebrow="05 · NETWORK HOTSPOTS"
          title="Highest-Entry Stations"
          description="Stations with available observations ranked by entries in the latest monitoring snapshot."
        />

        <DataTable
          columns={hotspotColumns}
          rows={monitoringHotspots.slice(0, 15)}
          emptyMessage="Hotspot rankings will appear after the first observation."
        />
      </section>

      <section className="analytics-section" id="flow">
        <SectionHeading
          eyebrow="06 · PASSENGER MOVEMENT"
          title="Passenger Flow"
          description="Station entries, exits, and net passenger flow."
        />

        <DataTable
          columns={flowColumns}
          rows={monitoringFlow}
          emptyMessage="Passenger-flow records will appear after the first observation."
        />
      </section>

      <section className="analytics-section" id="anomalies">
        <SectionHeading
          eyebrow="07 · DATA QUALITY"
          title="Statistical Outliers"
          description="Results returned by the existing statistical screening endpoint."
        />

        <ErrorMessage message={errors.anomalies} />

        <DataTable
          columns={[
            {
              key: "station",
              label: "Station",
              render: (_, row) =>
                row.station ?? row.Station ?? row.name ?? "—",
            },
            {
              key: "hour",
              label: "Hour",
              render: (_, row) => {
                const hour = row.hour ?? row.Hour;

                return hour == null ? "—" : `${hour}:00`;
              },
            },
            {
              key: "value",
              label: "Recorded value",
              render: (_, row) =>
                formatNumber(
                  row.ridership ?? row.Ridership ?? row.value
                ),
            },
            {
              key: "reason",
              label: "Screening detail",
              render: (_, row) =>
                row.reason ??
                row.anomaly_type ??
                row.status ??
                "Statistical outlier",
            },
          ]}
          rows={anomalies}
          emptyMessage="No outlier records were returned."
        />
      </section>

      <section
        className="analytics-section analytics-heatmap-section"
        id="heatmap"
      >
        <SectionHeading
          eyebrow="08 · STATION-HOUR PATTERNS"
          title="Station-Hour Heatmap"
          description="Station activity distributed across the 24 hours of the day."
          right={
            <span className="analytics-data-tag">
              {formatNumber(stationHourHeatmap.length)} stations
            </span>
          }
        />

        <div className="analytics-heatmap-summary">
          <div>
            <span className="analytics-summary-label">Hours displayed</span>
            <strong>00:00–23:00</strong>
          </div>

          <div>
            <span className="analytics-summary-label">Stations</span>
            <strong>{formatNumber(stationHourHeatmap.length)}</strong>
          </div>

          <div>
            <span className="analytics-summary-label">Monitoring hour</span>
            <strong>
              {getMonitoringHour(monitoring) == null
                ? "—"
                : `${String(
                    getMonitoringHour(monitoring)
                  ).padStart(2, "0")}:00`}
            </strong>
          </div>
        </div>

        <ErrorMessage message={errors.heatmap} />

        <Heatmap
          rows={stationHourHeatmap}
          valueLabel="recorded entries"
        />
      </section>

      <section className="analytics-section" id="models">
        <SectionHeading
          eyebrow="09 · MACHINE LEARNING"
          title="AI Model Insights"
          description="Model evaluation metrics returned by the analytics service."
        />

        <ErrorMessage message={errors.modelInsights} />

        <div className="analytics-model-grid">
          {modelMetrics.map((metric) => {
            let value = "—";

            if (metric.value !== null && metric.value !== undefined) {
              value =
                typeof metric.value === "number" &&
                metric.label !== "Model"
                  ? formatDecimal(metric.value, 4)
                  : String(metric.value);
            }

            return (
              <MetricCard
                key={metric.label}
                label={metric.label}
                value={value}
              />
            );
          })}
        </div>
      </section>

      <section className="analytics-section" id="recommendations">
        <SectionHeading
          eyebrow="10 · DECISION SUPPORT"
          title="Analytics-Driven Recommendations"
          description="Suggested follow-ups based on monitoring observations and statistical screening results."
          right={
            <span className="analytics-data-tag">
              {recommendations.length} suggestions
            </span>
          }
        />

        {recommendations.length === 0 ? (
          <EmptyState message="Recommendations will appear as monitoring data becomes available." />
        ) : (
          <div className="analytics-recommendations-grid">
            {recommendations.map((recommendation) => (
              <RecommendationCard
                key={recommendation.id}
                recommendation={recommendation}
              />
            ))}
          </div>
        )}
      </section>

      <footer className="analytics-page-footer">
        AI MetroFlow · Live Monitoring and Analytics
      </footer>
    </main>
  );
}
