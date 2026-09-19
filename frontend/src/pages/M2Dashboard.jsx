import React, { useEffect, useState } from "react";
import { request } from "../services/api";

export default function M2Dashboard() {
  const [peakHours, setPeakHours] = useState([]);
  const [traffic, setTraffic] = useState([]);

  const [demand, setDemand] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [delay, setDelay] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadM2Data() {
      try {
        const [peakResponse, trafficResponse] = await Promise.all([
          request("/api/peak-hours/summary"),
          request("/api/traffic/summary"),
        ]);

        setPeakHours(peakResponse.peak_hours || []);
        setTraffic(trafficResponse.traffic_analysis || []);

        const demandResponse = await request("/api/demand/predict", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
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
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            avg_ridership: 660,
            current_frequency: 10,
          }),
        });

        setSchedule(scheduleResponse);

        const delayResponse = await request("/api/delay/analyze", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
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
            headers: {
              "Content-Type": "application/json",
            },
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
      } catch (error) {
        console.error("M2 dashboard error:", error);
      } finally {
        setLoading(false);
      }
    }

    loadM2Data();
  }, []);

  if (loading) {
    return <div className="page-container">Loading M2 analytics...</div>;
  }

  return (
    <div className="page-container">
      <h1>M2 AI Analytics</h1>

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
            <strong>
              {delay?.delay_minutes ?? "N/A"} min
            </strong>
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
      </div>
    </div>
  );
}