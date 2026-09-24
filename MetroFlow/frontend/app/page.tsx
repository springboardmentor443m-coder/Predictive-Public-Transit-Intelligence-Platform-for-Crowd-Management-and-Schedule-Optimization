"use client";

import { useEffect, useState } from "react";

type PredictionResponse = {
  station: string;
  hour: number;
  current_ridership: number;
  predicted_next_hour_ridership: number;
  crowd_level: string;
  recommendation: string;
};

type AnalyticsResponse = {
  total_ridership: number;
  total_stations: number;
  busiest_station: string;
  peak_hour: number;
};

type WeatherResponse = {
  average_temperature: number;
  average_humidity: number;
  total_rainfall: number;
  average_wind_speed: number;
};

export default function Home() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [station, setStation] = useState("Attiguppe");
  const [hour, setHour] = useState(18);
  const [dayOfWeek, setDayOfWeek] = useState(1);
  const [currentRidership, setCurrentRidership] = useState(100);
  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/analytics");

        if (!response.ok) {
          throw new Error("Failed to fetch analytics");
        }

        const data: AnalyticsResponse = await response.json();
        setAnalytics(data);
      } catch (err) {
        console.error("Analytics fetch error:", err);
      }
    };

    const fetchWeather = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/weather-summary"
        );

        if (!response.ok) {
          throw new Error("Failed to fetch weather");
        }

        const data: WeatherResponse = await response.json();
        setWeather(data);
      } catch (err) {
        console.error("Weather fetch error:", err);
      }
    };

    fetchAnalytics();
    fetchWeather();
  }, []);

  const predictRidership = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          station,
          hour,
          day_of_week: dayOfWeek,
          current_ridership: currentRidership,
        }),
      });

      if (!response.ok) {
        throw new Error("Prediction request failed");
      }

      const data: PredictionResponse = await response.json();
      setResult(data);
    } catch {
      setError(
        "Unable to connect to MetroFlow API. Make sure the FastAPI server is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const getCrowdClass = (level: string) => {
    switch (level.toLowerCase()) {
      case "very high":
        return "crowd very-high";
      case "high":
        return "crowd high";
      case "medium":
        return "crowd medium";
      default:
        return "crowd low";
    }
  };

  return (
    <main className="dashboard">
      <header className="header">
        <div>
          <p className="eyebrow">AI-POWERED METRO INTELLIGENCE</p>
          <h1>MetroFlow</h1>
          <p className="subtitle">
            Predictive crowd management and demand intelligence
          </p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          API Ready
        </div>
      </header>

      <section className="hero">
        <div>
          <h2>Metro Ridership Prediction</h2>
          <p>
            Predict next-hour station demand using historical ridership
            patterns and operational features.
          </p>
        </div>
      </section>

      <section className="content-grid">
        <div className="card input-card">
        {analytics && (
  <section className="mb-8">
    <div className="mb-4">
      <h2 className="text-2xl font-bold text-slate-800">
        Metro Analytics
      </h2>
      <p className="text-slate-500">
        Insights from Bengaluru Metro ridership data
      </p>
    </div>

    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      
      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Total Ridership</p>
        <p className="mt-2 text-3xl font-bold text-slate-800">
          {analytics.total_ridership.toLocaleString()}
        </p>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Metro Stations</p>
        <p className="mt-2 text-3xl font-bold text-slate-800">
          {analytics.total_stations}
        </p>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Busiest Station</p>
        <p className="mt-2 text-lg font-bold text-slate-800">
          {analytics.busiest_station}
        </p>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Peak Hour</p>
        <p className="mt-2 text-3xl font-bold text-slate-800">
          {analytics.peak_hour}:00
        </p>
      </div>

    </div>
  </section>
)}

{weather && (
  <section className="mb-8">
    <div className="mb-4">
      <h2 className="text-2xl font-bold text-slate-800">
        Weather & Environmental Insights
      </h2>
      <p className="text-slate-500">
        Bengaluru weather conditions during operational period
      </p>
    </div>

    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Average Temperature</p>
        <p className="mt-2 text-3xl font-bold text-slate-800">
          {weather.average_temperature} °C
        </p>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Average Humidity</p>
        <p className="mt-2 text-3xl font-bold text-slate-800">
          {weather.average_humidity}%
        </p>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Total Rainfall</p>
        <p className="mt-2 text-3xl font-bold text-slate-800">
          {weather.total_rainfall} mm
        </p>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Average Wind Speed</p>
        <p className="mt-2 text-3xl font-bold text-slate-800">
          {weather.average_wind_speed} km/h
        </p>
      </div>
    </div>
  </section>
)}
          <h3>Prediction Input</h3>

          <label>Metro Station</label>
          <input
            value={station}
            onChange={(e) => setStation(e.target.value)}
            placeholder="Enter station"
          />

          <label>Hour of Day</label>
          <input
            type="number"
            min="0"
            max="23"
            value={hour}
            onChange={(e) => setHour(Number(e.target.value))}
          />

          <label>Day of Week</label>
          <select
            value={dayOfWeek}
            onChange={(e) => setDayOfWeek(Number(e.target.value))}
          >
            <option value={0}>Monday</option>
            <option value={1}>Tuesday</option>
            <option value={2}>Wednesday</option>
            <option value={3}>Thursday</option>
            <option value={4}>Friday</option>
            <option value={5}>Saturday</option>
            <option value={6}>Sunday</option>
          </select>

          <label>Current Ridership</label>
          <input
            type="number"
            min="0"
            value={currentRidership}
            onChange={(e) => setCurrentRidership(Number(e.target.value))}
          />

          <button onClick={predictRidership} disabled={loading}>
            {loading ? "Predicting..." : "Predict Next-Hour Demand"}
          </button>

          {error && <p className="error">{error}</p>}
        </div>

        <div className="card results-card">
          <h3>Prediction Results</h3>

          {!result && !loading && (
            <div className="empty-state">
              <div className="empty-icon">🚇</div>
              <p>Enter station information and run a prediction.</p>
            </div>
          )}

          {loading && (
            <div className="empty-state">
              <div className="empty-icon">🤖</div>
              <p>AI model is generating prediction...</p>
            </div>
          )}

          {result && (
            <>
              <div className="result-top">
                <div>
                  <p className="result-label">STATION</p>
                  <h2>{result.station}</h2>
                </div>

                <div className={getCrowdClass(result.crowd_level)}>
                  {result.crowd_level}
                </div>
              </div>

              <div className="metrics">
                <div className="metric">
                  <span>Current Ridership</span>
                  <strong>{result.current_ridership}</strong>
                </div>

                <div className="metric">
                  <span>Predicted Next Hour</span>
                  <strong>
                    {Math.round(result.predicted_next_hour_ridership)}
                  </strong>
                </div>

                <div className="metric">
                  <span>Prediction Hour</span>
                  <strong>{result.hour}:00</strong>
                </div>
              </div>

              <div className="recommendation">
                <p>OPERATIONAL RECOMMENDATION</p>
                <h4>{result.recommendation}</h4>
              </div>
            </>
          )}
        </div>
      </section>

      <footer>
        MetroFlow • AI-powered public transit intelligence platform
      </footer>
    </main>
  );
}