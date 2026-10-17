
import { useCallback, useEffect, useState } from "react";
import "../styles/StationIntelligence.css";

import {
  Activity,
  AlertTriangle,
  Brain,
  Gauge,
  RefreshCw,
  TrainFront,
  Clock3,
  CheckCircle2,
} from "lucide-react";

import { getStationOperations } from "../services/api";

const HISTORICAL_DATE = "2025-09-30";
const HISTORICAL_HOUR = 18;

const STATIONS = [
  "Mahatma Gandhi Road",
  "Benniganahalli",
  "Indiranagar",
  "Cubbon Park",
  "Trinity",
  "Banashankari",
  "Baiyappanahalli",
];

function formatNumber(value, decimals = 0) {
  if (
    value === null ||
    value === undefined ||
    value === "" ||
    !Number.isFinite(Number(value))
  ) {
    return "Unavailable";
  }

  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function formatPercent(value) {
  return value === null || value === undefined
    ? "Unavailable"
    : `${formatNumber(value, 2)}%`;
}

function MetricCard({ label, value, description, accent }) {
  return (
    <div className={`station-metric-card ${accent}`}>
      <span className="station-metric-label">{label}</span>
      <strong className="station-metric-value">{value}</strong>
      <span className="station-metric-description">
        {description}
      </span>
    </div>
  );
}

function getAssessment(score) {
  if (score === null || score === undefined || !Number.isFinite(Number(score))) {
    return {
      level: "UNAVAILABLE",
      title: "Pressure assessment unavailable",
      message:
        "A reliable pressure score is not available for this station and time. Review the available historical observations before making operational decisions.",
      className: "moderate",
    };
  }

  const value = Number(score);

  if (value >= 85) {
    return {
      level: "CRITICAL",
      title: "Very high analytical demand pressure",
      message:
        "The station has a very high network-based demand pressure score. Prioritize review of the historical demand pattern and consider whether additional crowd-management measures may be appropriate.",
      className: "critical",
    };
  }

  if (value >= 60) {
    return {
      level: "HIGH",
      title: "Elevated analytical demand pressure",
      message:
        "The historical demand indicators suggest elevated pressure. Review peak-period patterns and consider the available service-planning recommendations.",
      className: "high",
    };
  }

  if (value >= 30) {
    return {
      level: "MODERATE",
      title: "Moderate analytical demand pressure",
      message:
        "The station's analytical pressure score is moderate. Continue reviewing demand patterns and compare them with other historical periods.",
      className: "moderate",
    };
  }

  return {
    level: "LOW",
    title: "Lower analytical demand pressure",
    message:
      "The station's historical analytical pressure score is relatively low. This score is not a direct measurement of passenger occupancy or physical congestion.",
    className: "low",
  };
}

function StationIntelligence() {
  const [station, setStation] = useState(STATIONS[0]);
  const [stationData, setStationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadStationData = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getStationOperations(
        station,
        HISTORICAL_DATE,
        HISTORICAL_HOUR
      );

      if (!data || typeof data !== "object") {
        throw new Error("The API returned an invalid response.");
      }

      setStationData(data);
    } catch (err) {
      console.error("Failed to load station intelligence:", err);
      setStationData(null);

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Unable to load station intelligence data."
      );
    } finally {
      setLoading(false);
    }
  }, [station]);

  useEffect(() => {
    loadStationData();
  }, [loadStationData]);

  const monitoring = stationData?.monitoring ?? {};
  const alerts = stationData?.alerts ?? {};
  const scheduling = stationData?.scheduling ?? {};

  const currentRidership =
    monitoring.current_ridership ?? null;

  const predictedRidership =
    monitoring.predicted_next_hour_ridership ?? null;

  const observedRidership =
    monitoring.observed_next_hour_ridership ?? null;

  const pressureScore =
    monitoring.pressure_score ?? null;

  const pressureLevel =
    monitoring.congestion_level ?? "UNAVAILABLE";

  const predictionError =
    monitoring.prediction_error_percentage ?? null;

  const netFlow = monitoring.net_flow ?? null;
  const isPeakHour = monitoring.peak_hour ?? false;

  const alertList = Array.isArray(alerts.alerts)
    ? alerts.alerts
    : [];

  const alertCount =
    alerts.alert_count ?? alertList.length;

  const assessment = getAssessment(pressureScore);

  const predictionDifference =
    predictedRidership !== null && currentRidership !== null
      ? Number(predictedRidership) - Number(currentRidership)
      : null;

  const predictionTrend =
    predictionDifference === null
      ? "UNAVAILABLE"
      : predictionDifference > 0
        ? "INCREASING"
        : predictionDifference < 0
          ? "DECREASING"
          : "STABLE";

  const monitoringDate =
    monitoring.monitoring_date ??
    monitoring.latest_date ??
    HISTORICAL_DATE;

  const monitoringHour =
    monitoring.monitoring_hour ??
    monitoring.latest_hour ??
    HISTORICAL_HOUR;

  return (
    <main className="station-page">
      {/* HEADER */}
      <section className="station-header">
        <div>
          <div className="system-status">
            <span className="status-pulse" />
            STATION INTELLIGENCE
          </div>

          <h1>Station Intelligence</h1>

          <p>
            AI-powered station monitoring, prediction, alerts
            and scheduling decision support.
          </p>
        </div>

        <div className="station-mode-badge">
          <Clock3 size={17} />

          <div>
            <span>Monitoring mode</span>
            <strong>Historical replay</strong>
          </div>
        </div>
      </section>

      {/* STATION SELECTOR */}
      <section className="station-selector panel">
        <div>
          <span className="eyebrow">SELECT STATION</span>
          <h2>Station analysis</h2>
        </div>

        <div className="station-selector-controls">
          <select
            value={station}
            onChange={(event) => setStation(event.target.value)}
            disabled={loading}
            aria-label="Select station"
          >
            {STATIONS.map((stationName) => (
              <option key={stationName} value={stationName}>
                {stationName}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={loadStationData}
            disabled={loading}
            className="station-refresh-button"
          >
            <RefreshCw
              size={17}
              className={loading ? "spin" : ""}
            />

            {loading ? "Analyzing..." : "Analyze Station"}
          </button>
        </div>
      </section>

      {/* ERROR */}
      {error && (
        <div className="api-status error" role="alert">
          {error}
        </div>
      )}

      {/* LOADING */}
      {loading && (
        <div className="api-status" role="status">
          Analyzing historical data for{" "}
          <strong>{station}</strong>...
        </div>
      )}

      {/* STATION OVERVIEW */}
      {stationData && !loading && (
        <>
          <section className="station-overview">
            <div className="station-title-card">
              <div className="station-title-icon">
                <TrainFront size={26} />
              </div>

              <div>
                <span className="eyebrow">HISTORICAL ANALYSIS</span>

                <h2>{stationData.station ?? station}</h2>

                <p>
                  {monitoringDate}
                  {" • "}
                  {String(monitoringHour).padStart(2, "0")}:00
                </p>
              </div>
            </div>

            <div
              className={`station-pressure-badge ${
                String(pressureLevel).toLowerCase()
              }`}
            >
              <Gauge size={18} />

              <div>
                <span>Pressure</span>
                <strong>{pressureLevel}</strong>
              </div>
            </div>
          </section>

          {/* METRICS */}
          <section className="station-metrics-grid">
            <MetricCard
              label="Current Ridership"
              value={formatNumber(currentRidership)}
              description="Historical hourly entries"
              accent="blue"
            />

            <MetricCard
              label="AI Prediction"
              value={formatNumber(predictedRidership)}
              description="Estimated next-hour ridership"
              accent="purple"
            />

            <MetricCard
              label="Observed"
              value={formatNumber(observedRidership)}
              description="Observed next-hour ridership"
              accent="green"
            />

            <MetricCard
              label="Pressure Score"
              value={formatNumber(pressureScore, 2)}
              description="Analytical score out of 100"
              accent="orange"
            />
          </section>

          {/* AI OPERATIONAL ASSESSMENT */}
          <section className="panel station-assessment-panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">
                  AI OPERATIONAL ASSESSMENT
                </span>

                <h2>{assessment.title}</h2>
              </div>

              <div
                className={`panel-icon ${
                  assessment.className === "critical" ||
                  assessment.className === "high"
                    ? "red"
                    : "purple"
                }`}
              >
                <Brain size={19} />
              </div>
            </div>

            <div
              className={`station-assessment ${assessment.className}`}
            >
              <div className="station-assessment-status">
                <strong>{assessment.level}</strong>

                <span>Analytical pressure assessment</span>
              </div>

              <p>{assessment.message}</p>
            </div>

            <div className="station-assessment-signals">
              <div>
                <span>Prediction trend</span>
                <strong>{predictionTrend}</strong>
              </div>

              <div>
                <span>Alert signals</span>
                <strong>{formatNumber(alertCount)}</strong>
              </div>

              <div>
                <span>Peak period</span>
                <strong>
                  {isPeakHour === true
                    ? "YES"
                    : isPeakHour === false
                      ? "NO"
                      : "Unavailable"}
                </strong>
              </div>

              <div>
                <span>Net flow</span>
                <strong>{formatNumber(netFlow)}</strong>
              </div>
            </div>
          </section>

          {/* AI ANALYSIS + ALERTS */}
          <section className="station-content-grid">
            <article className="panel">
              <div className="panel-header">
                <div>
                  <span className="eyebrow">AI ANALYSIS</span>
                  <h2>Prediction Performance</h2>
                </div>

                <div className="panel-icon purple">
                  <Brain size={19} />
                </div>
              </div>

              <div className="station-analysis-list">
                <div>
                  <span>Prediction error</span>
                  <strong>{formatPercent(predictionError)}</strong>
                </div>

                <div>
                  <span>Net flow</span>
                  <strong>{formatNumber(netFlow)}</strong>
                </div>

                <div>
                  <span>Peak hour</span>
                  <strong>
                    {isPeakHour === true
                      ? "YES"
                      : isPeakHour === false
                        ? "NO"
                        : "Unavailable"}
                  </strong>
                </div>

                <div>
                  <span>Demand direction</span>
                  <strong>{predictionTrend}</strong>
                </div>
              </div>

              <p className="station-metric-description">
                Prediction error is shown only when the backend
                has both a prediction and an observed next-hour
                value. Unavailable error does not mean zero error.
              </p>
            </article>

            {/* ALERTS */}
            <article className="panel">
              <div className="panel-header">
                <div>
                  <span className="eyebrow">ALERTS</span>
                  <h2>Station Alerts</h2>
                </div>

                <div className="panel-icon red">
                  <AlertTriangle size={19} />
                </div>
              </div>

              <div className="station-alert-summary">
                <strong>{formatNumber(alertCount)}</strong>
                <span>active alert signals</span>
              </div>

              {alertList.length > 0 ? (
                <div className="station-alert-list">
                  {alertList.map((alert, index) => (
                    <div
                      className="station-alert"
                      key={
                        alert.id ??
                        `${alert.title ?? "alert"}-${index}`
                      }
                    >
                      <strong>
                        {alert.title ?? "Alert"}
                      </strong>

                      <p>
                        {alert.message ??
                          "No additional alert details available."}
                      </p>

                      {alert.recommendation && (
                        <small>{alert.recommendation}</small>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="station-no-alert">
                  <CheckCircle2 size={18} />

                  <span>
                    No alert records were returned for this station
                    and historical selection.
                  </span>
                </div>
              )}
            </article>
          </section>

          {/* SCHEDULING */}
          <section className="panel scheduling-panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">
                  SCHEDULING INTELLIGENCE
                </span>

                <h2>Service Recommendation</h2>
              </div>

              <div className="panel-icon blue">
                <Activity size={19} />
              </div>
            </div>

            {Object.keys(scheduling).length > 0 ? (
              <>
                <div className="scheduling-grid">
                  <div>
                    <span>Priority</span>
                    <strong>
                      {scheduling.priority_level ?? "Unavailable"}
                    </strong>
                  </div>

                  <div>
                    <span>Priority Score</span>
                    <strong>
                      {formatNumber(
                        scheduling.scheduling_priority_score,
                        2
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Current Headway</span>
                    <strong>
                      {scheduling.current_peak_median_headway_minutes ??
                        "Unavailable"}
                      {scheduling.current_peak_median_headway_minutes !=
                      null
                        ? " min"
                        : ""}
                    </strong>
                  </div>

                  <div>
                    <span>Recommended Headway</span>
                    <strong>
                      {scheduling.recommended_peak_headway_minutes ??
                        "Unavailable"}
                      {scheduling.recommended_peak_headway_minutes !=
                      null
                        ? " min"
                        : ""}
                    </strong>
                  </div>
                </div>

                {scheduling.action && (
                  <div className="scheduling-action">
                    <strong>Recommended analytical action</strong>
                    <p>{scheduling.action}</p>
                  </div>
                )}
              </>
            ) : (
              <p>
                No scheduling recommendation was returned for
                this station and historical selection.
              </p>
            )}

            <p className="station-metric-description">
              Recommendations are analytical decision support,
              not official BMRCL service instructions.
            </p>
          </section>

          {/* DATA SOURCE */}
          <footer className="station-footer">
            <span>AI MetroFlow</span>
            <span>Historical BMRCL demand replay</span>
            <span>Analytical decision support</span>
          </footer>
        </>
      )}
    </main>
  );
}

export default StationIntelligence;
