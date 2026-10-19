import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Clock3,
  RefreshCw,
  Search,
  TrainFront,
  TrendingUp,
  Users,
} from "lucide-react";

import {
  getNetworkOperations,
  getNetworkScheduling,
  getMetroRoutes,
  getRouteFrequency,
  getRouteTrips,
  getTripSchedule,
} from "../services/api";

import "../styles/TrainOperations.css";

const SELECTED_DATE = "2025-09-30";
const SELECTED_HOUR = 18;

const number = (value, digits = 0) => {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const parsed = Number(value);

  return Number.isFinite(parsed)
    ? parsed.toLocaleString("en-IN", {
        maximumFractionDigits: digits,
        minimumFractionDigits: digits,
      })
    : "—";
};

const priorityClass = (value) =>
  String(value || "unknown").toLowerCase();

function TrainOperations() {
  // Existing operations and scheduling data
  const [operations, setOperations] = useState(null);
  const [scheduling, setScheduling] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Existing filters
  const [search, setSearch] = useState("");
  const [pressureFilter, setPressureFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [activeTab, setActiveTab] = useState("stations");

  // GTFS scheduled-service data
  const [gtfsRoutes, setGtfsRoutes] = useState([]);
  const [selectedRouteId, setSelectedRouteId] = useState("");
  const [routeFrequency, setRouteFrequency] = useState([]);
  const [routeTrips, setRouteTrips] = useState([]);
  const [selectedTripId, setSelectedTripId] = useState("");
  const [tripSchedule, setTripSchedule] = useState([]);
  const [gtfsLoading, setGtfsLoading] = useState(false);
  const [gtfsError, setGtfsError] = useState("");
  const [tripScheduleLoading, setTripScheduleLoading] = useState(false);

  // Load existing monitoring and scheduling intelligence.
  const loadData = useCallback(async (signal) => {
    setLoading(true);
    setError("");

    try {
      const [operationData, schedulingData] = await Promise.all([
        getNetworkOperations(SELECTED_DATE, SELECTED_HOUR),
        getNetworkScheduling(),
      ]);

      if (signal?.aborted) return;

      setOperations(operationData?.monitoring ?? operationData);
      setScheduling(schedulingData);
    } catch (err) {
      if (signal?.aborted) return;

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to load train operations data. Please try again."
      );
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    loadData(controller.signal);

    return () => controller.abort();
  }, [loadData]);

  // Load the available GTFS routes.
  useEffect(() => {
    let cancelled = false;

    async function loadRoutes() {
      setGtfsLoading(true);
      setGtfsError("");

      try {
        const response = await getMetroRoutes();

        const routes = Array.isArray(response?.routes)
          ? response.routes
          : [];

        if (!cancelled) {
          setGtfsRoutes(routes);

          setSelectedRouteId((current) => {
            if (routes.some((route) => route.route_id === current)) {
              return current;
            }

            return routes[0]?.route_id ?? "";
          });
        }
      } catch (err) {
        if (!cancelled) {
          setGtfsError(
            err.response?.data?.detail ||
              "Unable to load scheduled routes. Check the backend and login session."
          );
        }
      } finally {
        if (!cancelled) {
          setGtfsLoading(false);
        }
      }
    }

    loadRoutes();

    return () => {
      cancelled = true;
    };
  }, []);

  // Load scheduled frequency and trips when the route changes.
  useEffect(() => {
    if (!selectedRouteId) {
      setRouteFrequency([]);
      setRouteTrips([]);
      setSelectedTripId("");
      return;
    }

    let cancelled = false;

    async function loadRouteDetails() {
      setGtfsLoading(true);
      setGtfsError("");
      setRouteFrequency([]);
      setRouteTrips([]);
      setTripSchedule([]);
      setSelectedTripId("");

      try {
        const [frequencyResponse, tripsResponse] = await Promise.all([
          getRouteFrequency(selectedRouteId),
          getRouteTrips(selectedRouteId),
        ]);

        if (cancelled) return;

        const frequency = Array.isArray(frequencyResponse?.frequency)
          ? frequencyResponse.frequency
          : [];

        const trips = Array.isArray(tripsResponse?.trips)
          ? tripsResponse.trips
          : [];

        setRouteFrequency(frequency);
        setRouteTrips(trips);
        setSelectedTripId(trips[0]?.trip_id ?? "");
      } catch (err) {
        if (!cancelled) {
          setGtfsError(
            err.response?.data?.detail ||
              "Unable to load route frequency and trip information."
          );
        }
      } finally {
        if (!cancelled) {
          setGtfsLoading(false);
        }
      }
    }

    loadRouteDetails();

    return () => {
      cancelled = true;
    };
  }, [selectedRouteId]);

  // Load the timetable for the selected trip.
  useEffect(() => {
    if (!selectedTripId) {
      setTripSchedule([]);
      setTripScheduleLoading(false);
      return;
    }

    let cancelled = false;

    async function loadTripSchedule() {
      setTripScheduleLoading(true);
      setTripSchedule([]);
      setGtfsError("");

      try {
        const response = await getTripSchedule(selectedTripId);

        if (!cancelled) {
          setTripSchedule(
            Array.isArray(response?.schedule) ? response.schedule : []
          );
        }
      } catch (err) {
        if (!cancelled) {
          setGtfsError(
            err.response?.data?.detail ||
              "Unable to load the selected trip timetable."
          );
        }
      } finally {
        if (!cancelled) {
          setTripScheduleLoading(false);
        }
      }
    }

    loadTripSchedule();

    return () => {
      cancelled = true;
    };
  }, [selectedTripId]);

  // Existing station snapshots.
  const snapshots = useMemo(
    () => operations?.station_snapshots ?? [],
    [operations]
  );

  // Existing service-planning recommendations.
  const recommendations = useMemo(
    () => scheduling?.recommendations ?? [],
    [scheduling]
  );

  const filteredStations = useMemo(() => {
    const query = search.trim().toLowerCase();

    return snapshots
      .filter((station) => {
        const matchesSearch =
          !query ||
          String(station.station || "").toLowerCase().includes(query);

        const matchesPressure =
          pressureFilter === "ALL" ||
          String(station.congestion_level || "").toUpperCase() ===
            pressureFilter;

        return matchesSearch && matchesPressure;
      })
      .sort(
        (a, b) =>
          Number(b.pressure_score || 0) -
          Number(a.pressure_score || 0)
      );
  }, [snapshots, search, pressureFilter]);

  const filteredRecommendations = useMemo(() => {
    const query = search.trim().toLowerCase();

    return recommendations.filter((station) => {
      const matchesSearch =
        !query ||
        String(station.station || "").toLowerCase().includes(query);

      const matchesPriority =
        priorityFilter === "ALL" ||
        String(station.priority_level || "").toUpperCase() ===
          priorityFilter;

      return matchesSearch && matchesPriority;
    });
  }, [recommendations, search, priorityFilter]);

  const highestDemand = operations?.highest_current_ridership;
  const pressureLevels = operations?.pressure_levels ?? {};

  const isHistoricalReplay =
    highestDemand?.assessment_type ===
      "historical-demand-pressure-replay" ||
    snapshots.some(
      (station) =>
        station.assessment_type === "historical-demand-pressure-replay"
    );

  const selectedRoute = gtfsRoutes.find(
    (route) => route.route_id === selectedRouteId
  );

  const selectedTrip = routeTrips.find(
    (trip) => trip.trip_id === selectedTripId
  );

  // Initial operations loading state.
  if (loading && !operations && !scheduling) {
    return (
      <div className="train-operations-page">
        <div className="to-state-card">
          <span className="to-spinner" />
          <h2>Loading train operations</h2>
          <p>
            Fetching station monitoring and scheduling intelligence…
          </p>
        </div>
      </div>
    );
  }

  // Initial operations error state.
  if (error && !operations && !scheduling) {
    return (
      <div className="train-operations-page">
        <div className="to-state-card to-error-state">
          <AlertTriangle size={30} />
          <h2>Unable to load operations</h2>
          <p>{error}</p>

          <button
            className="to-primary-button"
            onClick={() => loadData()}
          >
            <RefreshCw size={16} />
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <main className="train-operations-page">
      {/* Page header */}
      <header className="to-page-header">
        <div>
          <div className="to-eyebrow">
            <TrainFront size={15} />
            AI METROFLOW / OPERATIONS
          </div>

          <h1>Train Operations</h1>

          <p>
            Station demand monitoring, ML-based ridership predictions,
            and analytical service-planning recommendations.
          </p>
        </div>

        <button
          className="to-refresh-button"
          onClick={() => loadData()}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? "to-spinning" : ""}
          />
          {loading ? "Refreshing…" : "Refresh data"}
        </button>
      </header>

      {/* Monitoring data notice */}
      <section className="to-data-banner">
        <div className="to-banner-icon">
          <Activity size={20} />
        </div>

        <div>
          <strong>
            {isHistoricalReplay
              ? "Historical demand-pressure replay"
              : "Operations monitoring summary"}
          </strong>

          <p>
            Monitoring period: {operations?.monitoring_date || SELECTED_DATE}
            {" · "}
            {String(
              operations?.monitoring_hour ?? SELECTED_HOUR
            ).padStart(2, "0")}
            :00. These results are not live train positions or real-time
            service status.
          </p>
        </div>

        <span className="to-status-pill">API connected</span>
      </section>

      {error && (
        <div className="to-inline-error">
          <AlertTriangle size={16} />
          Some data could not be refreshed: {error}
        </div>
      )}

      {/* GTFS scheduled services */}
      <section className="to-gtfs-section">
        <div className="to-section-heading">
          <div>
            <h2>Scheduled Metro Services</h2>
            <p>
              Explore scheduled routes, service headways, trips, and
              stop-by-stop timetables from the available BMRCL GTFS feed.
            </p>
          </div>
        </div>

        {gtfsError && (
          <div className="to-gtfs-error" role="alert">
            {gtfsError}
          </div>
        )}

        {gtfsRoutes.length > 0 && (
          <div className="to-gtfs-route-tabs">
            {gtfsRoutes.map((route) => (
              <button
                key={route.route_id}
                type="button"
                className={`to-gtfs-route-button ${
                  selectedRouteId === route.route_id ? "active" : ""
                }`}
                onClick={() => setSelectedRouteId(route.route_id)}
                aria-pressed={selectedRouteId === route.route_id}
              >
                {route.route_short_name || route.route_id}
              </button>
            ))}
          </div>
        )}

        {gtfsLoading && (
          <div className="to-gtfs-loading">
            Loading scheduled service data…
          </div>
        )}

        {!gtfsLoading && !gtfsError && gtfsRoutes.length === 0 && (
          <div className="to-gtfs-empty">
            No metro routes were returned by the API. Check the backend
            GTFS data and login session.
          </div>
        )}

        {selectedRoute && (
          <>
            <div className="to-gtfs-meta">
              <strong>
                {selectedRoute.route_long_name ||
                  selectedRoute.route_short_name ||
                  selectedRoute.route_id}
              </strong>
              <span>Route ID: {selectedRoute.route_id}</span>
            </div>

            <h3>Scheduled Frequency</h3>

            {routeFrequency.length === 0 ? (
              <div className="to-gtfs-empty">
                {gtfsLoading
                  ? "Loading frequency records…"
                  : "No frequency records are available for this route."}
              </div>
            ) : (
              <div className="to-table-wrap">
                <table className="to-table">
                  <thead>
                    <tr>
                      <th>Trip / Destination</th>
                      <th>Direction</th>
                      <th>Start Time</th>
                      <th>End Time</th>
                      <th>Scheduled Headway</th>
                    </tr>
                  </thead>

                  <tbody>
                    {routeFrequency.map((item, index) => {
                      const seconds = Number(item.headway_secs);

                      const headway =
                        item.headway_minutes !== null &&
                        item.headway_minutes !== undefined
                          ? Number(item.headway_minutes)
                          : Number.isFinite(seconds) && seconds > 0
                            ? seconds / 60
                            : null;

                      return (
                        <tr
                          key={`${item.trip_id || "trip"}-${
                            item.start_time || ""
                          }-${index}`}
                        >
                          <td>
                            {item.trip_headsign ||
                              item.trip_id ||
                              "—"}
                          </td>

                          <td>{item.direction_id ?? "—"}</td>
                          <td>{item.start_time || "—"}</td>
                          <td>{item.end_time || "—"}</td>

                          <td>
                            {headway !== null &&
                            Number.isFinite(headway) &&
                            headway > 0
                              ? `${number(headway, 1)} min`
                              : "Not provided"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <p className="to-gtfs-note">
              Headway is the scheduled interval between services in
              the GTFS feed, not a live measurement of actual train
              arrivals. Long intervals may reflect different scheduled
              service periods and should be interpreted in context.
            </p>

            <div
              className="to-gtfs-meta"
              style={{ marginTop: 24 }}
            >
              <label htmlFor="to-trip-select">
                Select a trip to inspect its timetable
              </label>

              <select
                id="to-trip-select"
                className="to-gtfs-select"
                value={selectedTripId}
                onChange={(event) =>
                  setSelectedTripId(event.target.value)
                }
                disabled={routeTrips.length === 0 || gtfsLoading}
              >
                {routeTrips.length === 0 && (
                  <option value="">No trips available</option>
                )}

                {routeTrips.map((trip) => (
                  <option
                    key={trip.trip_id}
                    value={trip.trip_id}
                  >
                    {trip.trip_headsign || trip.trip_id}
                    {trip.direction_id !== undefined &&
                    trip.direction_id !== null
                      ? ` — Direction ${trip.direction_id}`
                      : ""}
                  </option>
                ))}
              </select>
            </div>

            {selectedTrip && (
              <p className="to-gtfs-note">
                Selected trip: {selectedTrip.trip_id}
                {selectedTrip.service_id
                  ? ` · Service ID: ${selectedTrip.service_id}`
                  : ""}
              </p>
            )}

            <h3>Stop-by-Stop Timetable</h3>

            {tripScheduleLoading ? (
              <div className="to-gtfs-loading">
                Loading trip timetable…
              </div>
            ) : tripSchedule.length === 0 ? (
              <div className="to-gtfs-empty">
                {routeTrips.length === 0
                  ? "No trips are available for this route."
                  : "No stop timetable records were returned for the selected trip."}
              </div>
            ) : (
              <div className="to-table-wrap">
                <table className="to-table">
                  <thead>
                    <tr>
                      <th>Stop Order</th>
                      <th>Station</th>
                      <th>Arrival</th>
                      <th>Departure</th>
                    </tr>
                  </thead>

                  <tbody>
                    {tripSchedule.map((stop, index) => (
                      <tr
                        key={`${stop.stop_sequence ?? index}-${
                          stop.stop_name || stop.station_name || ""
                        }`}
                      >
                        <td>{stop.stop_sequence ?? index + 1}</td>

                        <td>
                          <strong>
                            {stop.stop_name ||
                              stop.station_name ||
                              "Unknown station"}
                          </strong>
                        </td>

                        <td>{stop.arrival_time || "—"}</td>
                        <td>{stop.departure_time || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <p className="to-gtfs-note">
              This timetable represents scheduled stop times from the
              available feed. It does not confirm real-time train
              positions, actual arrival times, or current delays.
            </p>
          </>
        )}
      </section>

      {/* Network metric cards */}
      <section className="to-metric-grid">
        <article className="to-metric-card">
          <div className="to-metric-top">
            <span>Stations monitored</span>
            <span className="to-metric-icon blue">
              <TrainFront size={19} />
            </span>
          </div>

          <strong>{number(operations?.stations_monitored)}</strong>
          <p>Stations in the monitoring dataset</p>
        </article>

        <article className="to-metric-card">
          <div className="to-metric-top">
            <span>High-pressure stations</span>
            <span className="to-metric-icon red">
              <AlertTriangle size={19} />
            </span>
          </div>

          <strong>
            {number(operations?.high_pressure_stations)}
          </strong>
          <p>Stations flagged HIGH by monitoring</p>
        </article>

        <article className="to-metric-card">
          <div className="to-metric-top">
            <span>High scheduling priority</span>
            <span className="to-metric-icon orange">
              <TrendingUp size={19} />
            </span>
          </div>

          <strong>
            {number(
              scheduling?.high_priority_stations ??
                scheduling?.priority_counts?.HIGH
            )}
          </strong>
          <p>Stations prioritized for service planning</p>
        </article>

        <article className="to-metric-card">
          <div className="to-metric-top">
            <span>Recommended peak headway</span>
            <span className="to-metric-icon green">
              <Clock3 size={19} />
            </span>
          </div>

          <strong>
            {recommendations.length
              ? `${number(
                  recommendations[0]
                    .recommended_peak_headway_minutes
                )} min`
              : "—"}
          </strong>
          <p>For the first listed recommendation</p>
        </article>
      </section>

      {/* Network pressure distribution */}
      <section className="to-pressure-section">
        <div className="to-section-heading">
          <div>
            <h2>Network pressure distribution</h2>
            <p>
              Monitoring classification across the station network
            </p>
          </div>
        </div>

        <div className="to-pressure-grid">
          {["LOW", "MODERATE", "HIGH", "CRITICAL"].map((level) => (
            <button
              key={level}
              className={`to-pressure-card ${priorityClass(level)} ${
                pressureFilter === level ? "selected" : ""
              }`}
              onClick={() =>
                setPressureFilter((current) =>
                  current === level ? "ALL" : level
                )
              }
            >
              <span>{level}</span>
              <strong>{number(pressureLevels[level] ?? 0)}</strong>

              <span className="to-pressure-track">
                <span
                  style={{
                    width: `${
                      operations?.stations_monitored
                        ? (Number(pressureLevels[level] || 0) /
                            Number(operations.stations_monitored)) *
                          100
                        : 0
                    }%`,
                  }}
                />
              </span>

              <small>Click to filter stations</small>
            </button>
          ))}
        </div>
      </section>

      {/* Highest demand station */}
      {highestDemand && (
        <section className="to-highest-demand">
          <div className="to-highest-copy">
            <span className="to-section-kicker">
              HIGHEST CURRENT RIDERSHIP
            </span>

            <h2>{highestDemand.station}</h2>

            <p>
              Highest current ridership in the selected historical
              monitoring period.
            </p>
          </div>

          <div className="to-demand-stat">
            <span>Current ridership</span>
            <strong>
              {number(highestDemand.current_ridership)}
            </strong>
          </div>

          <div className="to-demand-stat">
            <span>ML predicted next hour</span>
            <strong>
              {number(
                highestDemand.ml_predicted_next_hour_ridership,
                2
              )}
            </strong>
          </div>

          <div className="to-demand-stat">
            <span>Observed next hour</span>
            <strong>
              {number(highestDemand.observed_next_hour_ridership)}
            </strong>
          </div>

          <div className="to-demand-stat">
            <span>Prediction error</span>
            <strong>
              {number(
                highestDemand.prediction_error_percentage,
                2
              )}
              %
            </strong>
          </div>
        </section>
      )}

      {/* Station operations table */}
      <section className="to-data-section">
        <div className="to-section-heading">
          <div>
            <h2>Station operations</h2>
            <p>
              Review current demand, predicted ridership, and pressure
              scores.
            </p>
          </div>

          <span className="to-result-count">
            {number(filteredStations.length)} stations
          </span>
        </div>

        <div className="to-toolbar">
          <div className="to-search-box">
            <Search size={17} />

            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search station name…"
              aria-label="Search station name"
            />
          </div>

          <select
            value={pressureFilter}
            onChange={(event) => setPressureFilter(event.target.value)}
            aria-label="Filter by congestion level"
          >
            <option value="ALL">All congestion levels</option>
            <option value="LOW">Low</option>
            <option value="MODERATE">Moderate</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>

        <div className="to-table-wrap">
          <table className="to-table">
            <thead>
              <tr>
                <th>Station</th>
                <th>Current</th>
                <th>ML predicted</th>
                <th>Observed</th>
                <th>Pressure score</th>
                <th>Congestion</th>
                <th>Prediction error</th>
              </tr>
            </thead>

            <tbody>
              {filteredStations.map((station) => (
                <tr key={station.station}>
                  <td>
                    <strong>{station.station}</strong>
                    <small>
                      Net flow: {number(station.net_flow)}
                    </small>
                  </td>

                  <td>{number(station.current_ridership)}</td>

                  <td>
                    {number(
                      station.ml_predicted_next_hour_ridership,
                      2
                    )}
                  </td>

                  <td>
                    {number(station.observed_next_hour_ridership)}
                  </td>

                  <td>
                    <span className="to-score">
                      {number(station.pressure_score, 2)}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`to-level-badge ${priorityClass(
                        station.congestion_level
                      )}`}
                    >
                      {station.congestion_level || "Unknown"}
                    </span>
                  </td>

                  <td>
                    {number(
                      station.prediction_error_percentage,
                      2
                    )}
                    %
                  </td>
                </tr>
              ))}

              {!filteredStations.length && (
                <tr>
                  <td colSpan="7" className="to-empty-cell">
                    {snapshots.length
                      ? "No stations match your search or filter."
                      : "No station snapshots were returned by the API."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <p className="to-table-note">
          Showing station snapshots returned by the monitoring API.
          Prediction error is the backend-reported percentage and may
          be signed or absolute depending on the backend calculation.
        </p>
      </section>

      {/* ML scheduling recommendations */}
      <section className="to-data-section">
        <div className="to-section-heading">
          <div>
            <h2>Service-planning recommendations</h2>
            <p>
              Analytical headway recommendations based on demand and
              service indicators, not automatic timetable changes.
            </p>
          </div>

          <span className="to-result-count">
            {number(filteredRecommendations.length)} recommendations
          </span>
        </div>

        <div className="to-priority-summary">
          <div>
            <span className="to-level-dot high" />
            <span>High priority</span>
            <strong>
              {number(scheduling?.high_priority_stations)}
            </strong>
          </div>

          <div>
            <span className="to-level-dot moderate" />
            <span>Moderate priority</span>
            <strong>
              {number(scheduling?.moderate_priority_stations)}
            </strong>
          </div>

          <div>
            <span className="to-level-dot low" />
            <span>Low priority</span>
            <strong>
              {number(scheduling?.low_priority_stations)}
            </strong>
          </div>
        </div>

        <div className="to-toolbar">
          <div className="to-search-box">
            <Search size={17} />

            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search recommendation station…"
              aria-label="Search recommendation station"
            />
          </div>

          <select
            value={priorityFilter}
            onChange={(event) => setPriorityFilter(event.target.value)}
            aria-label="Filter by scheduling priority"
          >
            <option value="ALL">All priorities</option>
            <option value="HIGH">High</option>
            <option value="MODERATE">Moderate</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div className="to-table-wrap">
          <table className="to-table">
            <thead>
              <tr>
                <th>Station</th>
                <th>Priority</th>
                <th>Priority score</th>
                <th>Current headway</th>
                <th>Recommended</th>
                <th>Demand / headway</th>
              </tr>
            </thead>

            <tbody>
              {filteredRecommendations.map((item) => (
                <tr key={item.station}>
                  <td>
                    <strong>{item.station}</strong>
                  </td>

                  <td>
                    <span
                      className={`to-level-badge ${priorityClass(
                        item.priority_level
                      )}`}
                    >
                      {item.priority_level}
                    </span>
                  </td>

                  <td>
                    {number(item.scheduling_priority_score, 3)}
                  </td>

                  <td>
                    {number(
                      item.current_peak_median_headway_minutes
                    )}{" "}
                    min
                  </td>

                  <td>
                    <span className="to-recommended-headway">
                      {number(
                        item.recommended_peak_headway_minutes
                      )}{" "}
                      min
                    </span>
                  </td>

                  <td>
                    {number(item.peak_demand_per_headway, 2)}
                  </td>
                </tr>
              ))}

              {!filteredRecommendations.length && (
                <tr>
                  <td colSpan="6" className="to-empty-cell">
                    No recommendations match your search or priority
                    filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <p className="to-table-note">
          Recommendations are analytical outputs. They do not represent
          confirmed changes to BMRCL train schedules.
        </p>
      </section>

      {/* Footer */}
      <footer className="to-footer">
        <span>
          <Users size={15} /> AI MetroFlow decision support
        </span>

        <span>
          <ArrowUpRight size={14} /> Predicted values are model outputs
        </span>

        <span>
          <ArrowDownRight size={14} /> Historical data replay
        </span>
      </footer>
    </main>
  );
}

export default TrainOperations;