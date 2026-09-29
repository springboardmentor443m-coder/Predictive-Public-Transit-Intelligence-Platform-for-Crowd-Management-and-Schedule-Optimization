import React, { useEffect, useState } from "react";
import { request } from "../services/api";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function M2Dashboard() {
  const [peakHours, setPeakHours] = useState([]);
  const [traffic, setTraffic] = useState([]);

  const [demand, setDemand] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [delay, setDelay] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  const [alerts, setAlerts] = useState([]);
  const [announcement, setAnnouncement] = useState(null);
  const [realtime, setRealtime] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [heatmap, setHeatmap] = useState([]);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [peakResponse, trafficResponse] = await Promise.all([
          request("/api/peak-hours/summary"),
          request("/api/traffic/summary"),
        ]);

        setPeakHours(peakResponse.peak_hours || []);
        setTraffic(trafficResponse.traffic_analysis || []);

        const demandResponse = await request("/api/demand/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            hour: 17,
            day_of_week: 2,
            day_of_year: 200,
            month: 7,
            lag_1: 650,
            lag_24: 500,
            lag_168: 550,
          }),
        });

        setDemand(demandResponse);

        const scheduleResponse = await request("/api/schedule/optimize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            avg_ridership: 660,
            current_frequency: 10,
          }),
        });

        setSchedule(scheduleResponse);

        const delayResponse = await request("/api/delay/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            delay_minutes: 12,
            scheduled_frequency: 10,
          }),
        });

        setDelay(delayResponse);

        const recommendationResponse = await request(
          "/api/recommendations/generate",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              predicted_ridership: 660,
              traffic_level: "high",
              delay_minutes: 12,
            }),
          }
        );

        setRecommendations(
          recommendationResponse.recommendations || []
        );

        const alertResponse = await request("/api/alerts/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            predicted_ridership: 800,
            traffic_level: "high",
            delay_minutes: 20,
          }),
        });

        setAlerts(alertResponse.alerts || []);

        const announcementResponse = await request(
          "/api/announcements/create",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              title: "Platform Safety Alert",
              message:
                "Please follow station staff instructions and move safely.",
              severity: "high",
              station: "Central Station",
            }),
          }
        );

        setAnnouncement(announcementResponse.announcement || null);

        const realtimeResponse = await request("/api/realtime/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            station: "Central Station",
            crowd_level: "high",
            train_status: "delayed",
            delay_minutes: 8,
          }),
        });

        setRealtime(realtimeResponse);

        const analyticsResponse = await request("/api/analytics/summary", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            total_passengers: 12424238,
            active_alerts: alertResponse.alert_count || 0,
            delayed_trains: 1,
            average_delay: 8,
            peak_crowd_level: "high",
          }),
        });

        setAnalytics(analyticsResponse.analytics || null);

        const heatmapResponse = await request("/api/heatmap/data");
        setHeatmap(heatmapResponse.heatmap || []);
      } catch (error) {
        console.error("M2/M3 dashboard error:", error);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="page-container">
        Loading AI MetroFlow analytics...
      </div>
    );
  }

  const maxIntensity = Math.max(
    ...heatmap.map((point) => Number(point.intensity) || 0),
    1
  );

  return (
    <div className="page-container">
      <h1>AI MetroFlow — M2 & M3 Analytics</h1>

      <div className="dashboard-grid">

        <section className="dashboard-card">
          <h2>Demand Forecast</h2>
          <div className="data-row">
            <span>Predicted Ridership</span>
            <strong>
              {demand?.predicted_ridership
                ? Number(demand.predicted_ridership).toFixed(0)
                : "N/A"}
            </strong>
          </div>
        </section>

        <section className="dashboard-card">
          <h2>Schedule Optimization</h2>

          <div className="data-row">
            <span>Demand Level</span>
            <strong>{schedule?.demand_level || "N/A"}</strong>
          </div>

          <div className="data-row">
            <span>Recommended Frequency</span>
            <strong>
              {schedule?.recommended_frequency_minutes
                ? `${schedule.recommended_frequency_minutes} min`
                : "N/A"}
            </strong>
          </div>

          <p>{schedule?.action || ""}</p>
        </section>

        <section className="dashboard-card">
          <h2>Delay Analysis</h2>

          <div className="data-row">
            <span>Delay</span>
            <strong>{delay?.delay_minutes ?? "N/A"} min</strong>
          </div>

          <div className="data-row">
            <span>Severity</span>
            <strong>{delay?.severity || "N/A"}</strong>
          </div>

          <p>{delay?.recommended_action || ""}</p>
        </section>

        <section className="dashboard-card">
          <h2>AI Recommendations</h2>

          {recommendations.map((item, index) => (
            <div className="data-row" key={index}>
              <span>🤖</span>
              <span>{item}</span>
            </div>
          ))}
        </section>

        <section className="dashboard-card">
          <h2>Peak Hours</h2>

          {peakHours.map((item) => (
            <div key={item.hour} className="data-row">
              <span>{String(item.hour).padStart(2, "0")}:00</span>
              <span>{item.demand_level}</span>
              <span>
                {Number(item.avg_ridership).toFixed(0)}
              </span>
            </div>
          ))}
        </section>

        <section className="dashboard-card">
          <h2>Traffic Analysis</h2>

          {traffic.slice(0, 10).map((item, index) => (
            <div key={index} className="data-row">
              <span>{item.line}</span>
              <span>{item.traffic_level}</span>
            </div>
          ))}
        </section>

        <section className="dashboard-card">
          <h2>🚨 Operational Alerts</h2>

          <div className="data-row">
            <span>Total Alerts</span>
            <strong>{alerts.length}</strong>
          </div>

          {alerts.map((alert, index) => (
            <div className="data-row" key={index}>
              <span>{alert.type}</span>
              <strong>{alert.severity}</strong>
            </div>
          ))}
        </section>

        <section className="dashboard-card">
          <h2>📢 Emergency Announcement</h2>

          {announcement ? (
            <>
              <div className="data-row">
                <span>Station</span>
                <strong>{announcement.station}</strong>
              </div>

              <div className="data-row">
                <span>Severity</span>
                <strong>{announcement.severity}</strong>
              </div>

              <p>{announcement.title}</p>
              <p>{announcement.message}</p>
            </>
          ) : (
            <p>No active announcement.</p>
          )}
        </section>

        <section className="dashboard-card">
          <h2>🟢 Real-Time Updates</h2>

          {realtime ? (
            <>
              <div className="data-row">
                <span>Station</span>
                <strong>{realtime.station}</strong>
              </div>

              <div className="data-row">
                <span>Crowd Level</span>
                <strong>{realtime.crowd_level}</strong>
              </div>

              <div className="data-row">
                <span>Train Status</span>
                <strong>{realtime.train_status}</strong>
              </div>

              <div className="data-row">
                <span>Delay</span>
                <strong>{realtime.delay_minutes} min</strong>
              </div>

              <div className="data-row">
                <span>Status</span>
                <strong>{realtime.status}</strong>
              </div>
            </>
          ) : (
            <p>No real-time data available.</p>
          )}
        </section>

        <section className="dashboard-card">
          <h2>📊 M3 Operational Analytics</h2>

          {analytics ? (
            <>
              <div className="data-row">
                <span>Total Passengers</span>
                <strong>
                  {Number(
                    analytics.total_passengers
                  ).toLocaleString()}
                </strong>
              </div>

              <div className="data-row">
                <span>Active Alerts</span>
                <strong>{analytics.active_alerts}</strong>
              </div>

              <div className="data-row">
                <span>Delayed Trains</span>
                <strong>{analytics.delayed_trains}</strong>
              </div>

              <div className="data-row">
                <span>Average Delay</span>
                <strong>
                  {analytics.average_delay_minutes} min
                </strong>
              </div>

              <div className="data-row">
                <span>Peak Crowd Level</span>
                <strong>{analytics.peak_crowd_level}</strong>
              </div>
            </>
          ) : (
            <p>No analytics available.</p>
          )}
        </section>

        <section className="dashboard-card heatmap-card">
          <h2>🔥 Metro Crowd Heatmap</h2>

          <div className="heatmap-info">
            Showing {heatmap.length} metro station locations
          </div>

          <MapContainer
            center={[40.735, -73.98]}
            zoom={11}
            scrollWheelZoom={true}
            className="metro-heatmap"
          >
            <TileLayer
              attribution='&copy; OpenStreetMap contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {heatmap.map((point, index) => {
              const intensity =
                Number(point.intensity) || 0;

              const normalized =
                intensity / maxIntensity;

              const radius =
                6 + normalized * 18;

              return (
                <CircleMarker
                  key={index}
                  center={[
                    Number(point.latitude),
                    Number(point.longitude),
                  ]}
                  radius={radius}
                  pathOptions={{
                    fillOpacity: 0.45 + normalized * 0.4,
                    weight: 1,
                  }}
                >
                  <Popup>
                    <strong>{point.station}</strong>
                    <br />
                    Crowd intensity:{" "}
                    {Math.round(intensity).toLocaleString()}
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>
        </section>

      </div>
    </div>
  );
}