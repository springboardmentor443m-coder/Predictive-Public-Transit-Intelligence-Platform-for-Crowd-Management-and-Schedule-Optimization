import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Activity,
  AlertTriangle,
  Brain,
  TrainFront,
  TrendingUp,
  RefreshCw,
  ArrowRight,
  BarChart3,
  Bell,
  Database,
  Map,
  ShieldAlert,
  CircleDot,
} from "lucide-react";

import {
  getNetworkOperations,
  getDemandForecast,
} from "../services/api";

import "../styles/OperationsDashboard.css";


/* =========================================================
   HELPERS
   ========================================================= */

function formatNumber(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  return Math.round(Number(value)).toLocaleString();
}


function getPressureClass(level) {
  switch (String(level).toUpperCase()) {
    case "CRITICAL":
      return "critical";

    case "HIGH":
      return "high";

    case "MODERATE":
      return "moderate";

    default:
      return "low";
  }
}


/* =========================================================
   KPI CARD
   ========================================================= */

function KpiCard({
  icon: Icon,
  label,
  value,
  description,
  trend,
  accent,
}) {
  return (
    <div className={`ops-kpi-card ${accent}`}>
      <div className="ops-kpi-top">

        <div className="ops-kpi-icon">
          <Icon size={19} />
        </div>

        {trend && (
          <span className="ops-kpi-trend">
            <TrendingUp size={13} />
            {trend}
          </span>
        )}

      </div>

      <span className="ops-kpi-label">
        {label}
      </span>

      <strong className="ops-kpi-value">
        {value}
      </strong>

      <span className="ops-kpi-description">
        {description}
      </span>
    </div>
  );
}


/* =========================================================
   NETWORK NODE
   ========================================================= */

function NetworkNode({
  station,
  index,
  selected,
  onClick,
}) {
  const pressureClass = getPressureClass(
    station?.congestion_level
  );

  const positions = [
    { left: "8%", top: "48%" },
    { left: "18%", top: "30%" },
    { left: "30%", top: "30%" },
    { left: "42%", top: "30%" },
    { left: "54%", top: "30%" },
    { left: "66%", top: "30%" },
    { left: "78%", top: "48%" },
    { left: "66%", top: "67%" },
    { left: "54%", top: "67%" },
    { left: "42%", top: "67%" },
    { left: "30%", top: "67%" },
    { left: "18%", top: "67%" },
  ];

  const position =
    positions[index % positions.length];

  return (
    <button
      type="button"
      className={`network-node ${pressureClass} ${
        selected ? "selected" : ""
      }`}
      style={position}
      onClick={() => onClick(station)}
      title={`View ${station.station}`}
    >
      <span className="network-node-core">
        <CircleDot size={12} />
      </span>

      <span className="network-node-label">
        {station.station}
      </span>
    </button>
  );
}


/* =========================================================
   MAIN DASHBOARD
   ========================================================= */

function Dashboard() {
  const navigate = useNavigate();

  const [operationsData, setOperationsData] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [apiError, setApiError] =
    useState("");

  const [selectedStation, setSelectedStation] =
    useState(null);


  /* =======================================================
     LOAD NETWORK INTELLIGENCE
     ======================================================= */

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setApiError("");

      const [operations, demand] =
        await Promise.all([
          getNetworkOperations(
            "2025-09-30",
            18
          ),
          getDemandForecast(),
        ]);

      setOperationsData({
        ...operations,
        demandForecast: demand,
      });

    } catch (error) {
      console.error(
        "Failed to load dashboard data:",
        error
      );

      setApiError(
        "Unable to load network intelligence data."
      );

    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadDashboardData();
  }, []);


  /* =======================================================
     NETWORK INTELLIGENCE
     ======================================================= */

  const pressureCounts =
    operationsData?.pressure_counts || {
      LOW: 0,
      MODERATE: 0,
      HIGH: 0,
      CRITICAL: 0,
    };


  const stationsMonitored =
    operationsData?.stations_monitored || 0;


  const alertSummary =
    operationsData?.alerts || {};


  const activeAlerts =
    alertSummary?.total_alerts || 0;


  const severityCounts =
    alertSummary?.severity_counts || {};


  const stationSnapshots =
    operationsData?.monitoring
      ?.station_snapshots || [];


  const predictedDemand =
    operationsData?.demandForecast?.predicted_ridership ??
    operationsData?.demandForecast?.predicted_demand ??
    operationsData?.monitoring?.predicted_network_demand ??
    null;


  const totalStations =
    pressureCounts.LOW +
    pressureCounts.MODERATE +
    pressureCounts.HIGH +
    pressureCounts.CRITICAL;


  /* =======================================================
     PRIORITY STATION
     ======================================================= */

  const priorityStation =
    useMemo(() => {
      return [...stationSnapshots].sort(
        (a, b) =>
          (b.pressure_score || 0) -
          (a.pressure_score || 0)
      )[0] || null;
    }, [stationSnapshots]);


  /* =======================================================
     DEFAULT SELECTED STATION
     ======================================================= */

  useEffect(() => {
    if (
      !selectedStation &&
      priorityStation
    ) {
      setSelectedStation(
        priorityStation
      );
    }
  }, [
    priorityStation,
    selectedStation,
  ]);


  const activeStation =
    selectedStation ||
    priorityStation;


  /* =======================================================
     SELECTED STATION VALUES
     ======================================================= */

  const currentRidership =
    activeStation?.current_ridership || 0;


  const predictedRidership =
    activeStation
      ?.predicted_next_hour_ridership || 0;
  const pressureScore =
    activeStation?.pressure_score || 0;
  const netFlow =
    activeStation?.net_flow || 0;


  const congestionLevel =
    activeStation?.congestion_level ||
    "UNKNOWN";


  /* =======================================================
     AI ASSESSMENT
     ======================================================= */

  const assessment = (() => {
    const score = Number(pressureScore);

    if (
      !activeStation ||
      activeStation.congestion_level === "UNAVAILABLE" ||
      activeStation.pressure_score == null ||
      !Number.isFinite(score)
    ) {
      return {
        className: "moderate",
        title: "Station assessment unavailable",
        message:
          "Station pressure data is unavailable. Review the available station metrics.",
      };
    }

    if (score >= 85) {
      return {
        className: "critical",
        title: "Immediate operational attention required",
        message:
          "Critical demand pressure detected. Prioritize crowd-management measures and peak service requirements.",
      };
    }

    if (score >= 60) {
      return {
        className: "high",
        title: "Elevated station pressure detected",
        message:
          "Demand pressure is high. Review peak-period monitoring and service-frequency recommendations.",
      };
    }

    if (score >= 30) {
      return {
        className: "moderate",
        title: "Moderate operational pressure",
        message:
          "Demand pressure is moderate. Continue monitoring demand patterns and potential peak-period increases.",
      };
    }

    return {
      className: "low",
      title: "Station operating under lower pressure",
      message:
        "The analytical pressure score is relatively low. Continue routine station monitoring.",
    };
  })();


  /* =======================================================
     RECOMMENDED ACTION
     ======================================================= */

  const stationRecommendation =
    operationsData?.scheduling?.recommendations?.find(
      (item) => item.station === activeStation?.station
    ) ||
    operationsData?.scheduling?.recommendations?.find(
      (item) => item.station === priorityStation?.station
    );

  const recommendedAction = stationRecommendation
    ? `Review the recommended peak headway of ${stationRecommendation.recommended_peak_headway_minutes} minutes`
    : "No matching scheduling recommendation available";


  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <div className="operations-shell">

      <main className="operations-main">

        {/* TOP HEADER */}

        <header className="operations-header">

          <div>

            <div className="operations-breadcrumb">
              AI METROFLOW
              <span>/</span>
              OVERVIEW
            </div>

            <h1>
              Executive Operations Overview
            </h1>

            <p>
              AI-powered BMRCL network intelligence,
              demand prediction and operational
              decision support.
            </p>

          </div>


          <div className="operations-header-actions">

            <div className="feed-status">

              <span className="feed-pulse" />

              <div>
                <span>NETWORK STATUS</span>

                <strong>
                  Operational Monitoring
                </strong>
              </div>

            </div>


            <button
              type="button"
              className="refresh-stream-button"
              onClick={loadDashboardData}
              disabled={loading}
            >

              <RefreshCw
                size={16}
                className={
                  loading
                    ? "refresh-spinning"
                    : ""
                }
              />

              {loading
                ? "Analyzing..."
                : "Refresh Network Data"}

            </button>

          </div>

        </header>


        {/* API STATUS */}

        {apiError && (
          <div className="operations-error">

            <AlertTriangle size={17} />

            {apiError}

          </div>
        )}


        {/* KPI ROW */}

        <section className="operations-kpi-grid">

          <KpiCard
            icon={TrainFront}
            label="System Stations"
            value={stationsMonitored}
            description="BMRCL stations monitored"
            trend="83 network nodes"
            accent="blue"
          />


          <KpiCard
            icon={Activity}
            label="Network Pressure"
            value={
              pressureCounts.HIGH +
              pressureCounts.CRITICAL
            }
            description="High / critical pressure stations"
            trend={
              pressureCounts.CRITICAL > 0
                ? `${pressureCounts.CRITICAL} critical`
                : "No critical"
            }
            accent="orange"
          />


          <KpiCard
            icon={ShieldAlert}
            label="Active Alerts"
            value={activeAlerts}
            description="Network alert signals"
            trend={`${severityCounts.HIGH || 0} high`}
            accent="red"
          />


          <KpiCard
            icon={TrendingUp}
            label="AI Demand Forecast"
            value={formatNumber(predictedDemand)}
            description="Predicted next-calendar-day passengers"
            trend="XGBoost"
            accent="purple"
          />

        </section>


        {/* NETWORK + TELEMETRY */}

        <section
          id="network-telemetry"
          className="telemetry-layout"
        >

          <article className="network-telemetry-panel">

            <div className="section-heading">

              <div>

                <span className="section-eyebrow">
                  NETWORK TELEMETRY
                </span>

                <h2>
                  Interactive Network Operations Map
                </h2>

                <p>
                  Select a station to inspect its
                  AI-powered operational state.
                </p>

              </div>


              <div className="network-map-status">

                <span className="feed-pulse" />

                Network Activity

              </div>

            </div>


            <div className="network-map">

              <div className="map-grid" />

              <div className="route-line route-line-main" />
              <div className="route-line route-line-upper" />
              <div className="route-line route-line-lower" />


              {stationSnapshots
                .slice(0, 12)
                .map(
                  (station, index) => (
                    <NetworkNode
                      key={station.station}
                      station={station}
                      index={index}
                      selected={
                        activeStation?.station ===
                        station.station
                      }
                      onClick={
                        setSelectedStation
                      }
                    />
                  )
                )}


              {!stationSnapshots.length && (
                <div className="network-empty">

                  <Map size={32} />

                  <strong>
                    Network telemetry unavailable
                  </strong>

                  <span>
                    Waiting for network intelligence data.
                  </span>

                </div>
              )}


              <div className="network-map-legend">

                <div>
                  <span className="legend-node low" />
                  Low
                </div>

                <div>
                  <span className="legend-node moderate" />
                  Moderate
                </div>

                <div>
                  <span className="legend-node high" />
                  High
                </div>

                <div>
                  <span className="legend-node critical" />
                  Critical
                </div>

              </div>

            </div>

          </article>


          {/* STATION TELEMETRY */}

          <article className="station-telemetry-panel">

            <div className="section-heading compact">

              <div>

                <span className="section-eyebrow">
                  STATION TELEMETRY
                </span>

                <h2>
                  {activeStation?.station ||
                    "No station selected"}
                </h2>

              </div>

            </div>


            <div
              className={`telemetry-status ${
                getPressureClass(
                  congestionLevel
                )
              }`}
            >

              <span className="telemetry-status-dot" />

              <strong>
                {congestionLevel}
              </strong>

              <span>
                PRESSURE
              </span>

            </div>


            <div className="telemetry-primary-stat">

              <span>
                Pressure Score
              </span>

              <strong>
                {Number(
                  pressureScore
                ).toFixed(2)}
              </strong>


              <div className="telemetry-score-track">

                <div
                  className={`telemetry-score-fill ${
                    getPressureClass(
                      congestionLevel
                    )
                  }`}
                  style={{
                    width: `${Math.min(
                      Number(pressureScore),
                      100
                    )}%`,
                  }}
                />

              </div>

            </div>


            <div className="telemetry-stat-grid">

              <div>
                <span>Current</span>

                <strong>
                  {formatNumber(
                    currentRidership
                  )}
                </strong>

                <small>
                  passengers
                </small>
              </div>


              <div>
                <span>AI Prediction</span>

                <strong>
                  {formatNumber(
                    predictedRidership
                  )}
                </strong>

                <small>
                  next hour
                </small>
              </div>
<div>
                <span>Net Flow</span>

                <strong>
                  {netFlow >= 0 ? "+" : ""}
                  {formatNumber(netFlow)}
                </strong>

                <small>
                  passengers
                </small>
              </div>

            </div>


            <div className="telemetry-divider" />
<div className="telemetry-detail-row">

              <span>
                Peak period
              </span>

              <strong>
                {activeStation?.peak_hour
                  ? "YES"
                  : "NO"}
              </strong>

            </div>


            <button
              type="button"
              className="station-details-button"
              onClick={() =>
                navigate(
                  "/station-intelligence"
                )
              }
            >
              Open Station Intelligence

              <ArrowRight size={16} />

            </button>

          </article>

        </section>


        {/* AI INSIGHTS */}

        <section
          id="ai-insights"
          className="insights-layout"
        >

          <article className="ai-insight-panel">

            <div className="section-heading">

              <div>

                <span className="section-eyebrow">
                  AI OPERATIONAL INTELLIGENCE
                </span>

                <h2>
                  Recommended Operational Action
                </h2>

              </div>


              <div className="ai-heading-icon">
                <Brain size={19} />
              </div>

            </div>


            <div
              className={`ai-assessment ${
                assessment.className
              }`}
            >

              <div className="ai-assessment-icon">

                {assessment.className ===
                "critical" ? (
                  <AlertTriangle size={22} />
                ) : (
                  <Brain size={22} />
                )}

              </div>


              <div>

                <span className="ai-assessment-level">
                  {assessment.className.toUpperCase()}
                </span>

                <h3>
                  {assessment.title}
                </h3>

                <p>
                  {assessment.message}
                </p>

              </div>

            </div>


            <div className="ai-action-row">

              <div>

                <span>
                  Priority Station
                </span>

                <strong>
                  {priorityStation?.station ||
                    "—"}
                </strong>

              </div>


              <div>

                <span>
                  Pressure
                </span>

                <strong>
                  {Number(
                    priorityStation?.pressure_score ||
                    0
                  ).toFixed(2)}
                </strong>

              </div>


              <div>

                <span>
                  Recommended Action
                </span>

                <strong>
                  {recommendedAction}
                </strong>

              </div>

            </div>

          </article>


          {/* ALERTS */}

          <article
            id="alerts-center"
            className="alerts-panel"
          >

            <div className="section-heading compact">

              <div>

                <span className="section-eyebrow">
                  ALERT CENTER
                </span>

                <h2>
                  Network Signals
                </h2>

              </div>

              <Bell size={19} />

            </div>


            <div className="alert-summary-grid">

              <div className="alert-summary critical">

                <span>
                  Critical
                </span>

                <strong>
                  {severityCounts.CRITICAL || 0}
                </strong>

              </div>


              <div className="alert-summary high">

                <span>
                  High
                </span>

                <strong>
                  {severityCounts.HIGH || 0}
                </strong>

              </div>


              <div className="alert-summary moderate">

                <span>
                  Moderate
                </span>

                <strong>
                  {severityCounts.MODERATE || 0}
                </strong>

              </div>

            </div>


            <div className="alert-total">

              <span>
                Total active signals
              </span>

              <strong>
                {activeAlerts}
              </strong>

            </div>

          </article>

        </section>


        {/* ANALYTICS */}

        <section
          id="network-analytics"
          className="analytics-section"
        >

          <div className="section-heading">

            <div>

              <span className="section-eyebrow">
                NETWORK ANALYTICS
              </span>

              <h2>
                Pressure Distribution
              </h2>

            </div>

            <BarChart3 size={19} />

          </div>


          <div className="analytics-bars">

            {[
              {
                label: "Low",
                value: pressureCounts.LOW,
                className: "low",
              },
              {
                label: "Moderate",
                value: pressureCounts.MODERATE,
                className: "moderate",
              },
              {
                label: "High",
                value: pressureCounts.HIGH,
                className: "high",
              },
              {
                label: "Critical",
                value: pressureCounts.CRITICAL,
                className: "critical",
              },
            ].map((item) => {

              const percentage =
                totalStations > 0
                  ? (item.value /
                      totalStations) *
                    100
                  : 0;

              return (
                <div
                  className="analytics-bar-item"
                  key={item.label}
                >

                  <div className="analytics-bar-label">

                    <span>
                      {item.label}
                    </span>

                    <strong>
                      {item.value}
                    </strong>

                  </div>


                  <div className="analytics-bar-track">

                    <div
                      className={`analytics-bar-fill ${item.className}`}
                      style={{
                        width: `${percentage}%`,
                      }}
                    />

                  </div>


                  <small>
                    {percentage.toFixed(1)}%
                    {" "}of monitored stations
                  </small>

                </div>
              );
            })}

          </div>

        </section>


        {/* SCHEDULING */}

        <section
          id="scheduling"
          className="scheduling-strip"
        >

          <div className="scheduling-icon">
            <TrainFront size={20} />
          </div>


          <div>

            <span className="section-eyebrow">
              SCHEDULING INTELLIGENCE
            </span>

            <h3>
              Demand-based service optimization
            </h3>

            <p>
              AI MetroFlow combines station demand
              intensity, demand concentration and
              service-gap analysis to prioritize
              frequency interventions.
            </p>

          </div>


          <button
            type="button"
            onClick={() =>
              navigate(
                "/station-intelligence"
              )
            }
          >

            View Station Intelligence

            <ArrowRight size={16} />

          </button>

        </section>


        {/* DATASET STATUS */}

        <section
          id="datasets"
          className="dataset-status"
        >

          <div>

            <Database size={18} />

            <div>

              <strong>
                BMRCL Intelligence Dataset
              </strong>

              <span>
                Demand, passenger flow and GTFS scheduling data
              </span>

            </div>

          </div>


          <span className="dataset-badge">
            AI-POWERED INTELLIGENCE
          </span>

        </section>


        {/* FOOTER */}

        <footer className="operations-footer">

          <span>
            AI METROFLOW
          </span>

          <span>
            Predictive Public Transit Intelligence Platform
          </span>

          <span>
            AI-Powered Network Intelligence
          </span>

        </footer>

      </main>

    </div>
  );
}


export default Dashboard;
