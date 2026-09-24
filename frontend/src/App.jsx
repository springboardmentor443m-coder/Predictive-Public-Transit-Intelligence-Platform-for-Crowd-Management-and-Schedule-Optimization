import { useEffect, useState } from "react";
import "./App.css";
import metroCrowdImage from "./assets/images1.jpg";
import metroflowHome from "./assets/metroflow-home.png";

function App() {
  const [role, setRole] = useState("Operator");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loggedIn, setLoggedIn] = useState(false);
  const [page, setPage] = useState("home");
  const [stations, setStations] = useState([
    {
      name: "Central Station",
      passengers: 850,
      inflow: 500,
      outflow: 350,
      crowd: "High",
      status: "Congested",
    },
    {
      name: "City Square",
      passengers: 420,
      inflow: 230,
      outflow: 190,
      crowd: "Medium",
      status: "Normal",
    },
    {
      name: "North Station",
      passengers: 150,
      inflow: 80,
      outflow: 70,
      crowd: "Low",
      status: "Normal",
    },
    {
      name: "Airport Station",
      passengers: 680,
      inflow: 390,
      outflow: 290,
      crowd: "High",
      status: "Congested",
    },
  ]);

  const [stationsLoading, setStationsLoading] = useState(false);
  const [stationsError, setStationsError] = useState("");

  useEffect(() => {
    if (!loggedIn) {
      return;
    }

    const loadStations = async () => {
      setStationsLoading(true);
      setStationsError("");

      try {
        const response = await fetch("http://127.0.0.1:8000/stations");

        if (!response.ok) {
          throw new Error("Unable to load station data");
        }

        const data = await response.json();
        setStations(data);
      } catch {
        setStationsError("Showing demo data. Start the backend for live data.");
      } finally {
        setStationsLoading(false);
      }
    };

    loadStations();
  }, [loggedIn]);

  // ---------------- LOGIN ----------------

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          password: password,
          role: role,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setLoggedIn(true);
        setPage("home");
      } else {
        alert(data.message);
      }
    } catch {
      alert("Unable to connect to MetroFlow backend");
    }
  };

  // ---------------- LOGOUT ----------------

  const handleLogout = () => {
    setLoggedIn(false);
    setEmail("");
    setPassword("");
    setPage("home");
  };

  // ---------------- STATION DATA ----------------

  const totalPassengers = stations.reduce(
    (total, station) => total + station.passengers,
    0
  );

  const highCrowdStations = stations.filter(
    (station) => station.crowd === "High"
  ).length;

  const congestedStations = stations.filter(
    (station) => station.status === "Congested"
  ).length;

  // ---------------- LOGIN PAGE ----------------

  if (!loggedIn) {
    return (
      <div className="login-page">

        <div className="login-card">

          <div className="login-brand">
            <img
              src={metroflowHome}
              alt="MetroFlow smart transit network"
              className="login-brand-image"
            />

            <div className="login-brand-content">
            <div className="logo">🚆</div>

            <h1>MetroFlow</h1>

            <p>
              Predictive Public Transit
              <br />
              Intelligence Platform
            </p>
            </div>
          </div>

          <div className="login-form-section">

            <h2>Welcome Back</h2>

            <p className="login-subtitle">
              Sign in to access MetroFlow
            </p>

            <form onSubmit={handleLogin}>

              <label>Email</label>

              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <label>Password</label>

              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />

              <label>Login Role</label>

              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="Operator">Operator</option>
                <option value="Admin">Admin</option>
              </select>

              <button type="submit" className="login-button">
                Login
              </button>

            </form>

          </div>

        </div>

      </div>
    );
  }

  // ---------------- MAIN APPLICATION ----------------

  return (
    <div className="main-app">

      {/* HEADER */}

      <header className="navbar">

        <div
          className="nav-logo"
          onClick={() => setPage("home")}
        >
          🚆 <span>MetroFlow</span>
        </div>

        <nav>

          <button
            className={page === "home" ? "active-nav" : ""}
            onClick={() => setPage("home")}
          >
            Home
          </button>

          <button
            className={page === "crowd" ? "active-nav" : ""}
            onClick={() => setPage("crowd")}
          >
            Crowd Monitoring
          </button>

          <button
            className={page === "schedule" ? "active-nav" : ""}
            onClick={() => setPage("schedule")}
          >
            Scheduling
          </button>

          <button
            className={page === "prediction" ? "active-nav" : ""}
            onClick={() => setPage("prediction")}
          >
            AI Prediction
          </button>

          <button
            className={page === "alerts" ? "active-nav" : ""}
            onClick={() => setPage("alerts")}
          >
            Alerts
          </button>

          <button
            className={page === "analytics" ? "active-nav" : ""}
            onClick={() => setPage("analytics")}
          >
            Analytics
          </button>

        </nav>

        <div className="nav-user">

          <span>
            {role}
          </span>

          <button
            className="logout-button"
            onClick={handleLogout}
          >
            Logout
          </button>

        </div>

      </header>


      {/* ================= HOME ================= */}

      {page === "home" && (

        <main className="home-page">

          <section className="hero">

            <img
              src={metroflowHome}
              alt="MetroFlow Public Transit"
              className="hero-image"
            />

            <div className="hero-overlay">

              <h1>
                Smarter Transit.
                <br />
                Better Decisions.
              </h1>

              <p>
                Predictive intelligence for modern
                public transportation.
              </p>

            </div>

          </section>


          <section className="quote-section">

            <h2>
              “Monitor. Analyze. Optimize. Move Smarter.”
            </h2>

            <p>
              MetroFlow helps transit operators understand
              passenger movement, identify congestion and
              make intelligent operational decisions.
            </p>

          </section>


          <section className="modules">

            <h2>MetroFlow Intelligence Modules</h2>

            <div className="module-grid">

              <div
                className="module-card"
                onClick={() => setPage("crowd")}
              >
                <span>👥</span>
                <h3>Crowd Monitoring</h3>
                <p>
                  Monitor passenger density and
                  station congestion.
                </p>
              </div>


              <div
                className="module-card"
                onClick={() => setPage("schedule")}
              >
                <span>🚆</span>
                <h3>Scheduling</h3>
                <p>
                  Improve transit schedules and
                  service frequency.
                </p>
              </div>


              <div
                className="module-card"
                onClick={() => setPage("prediction")}
              >
                <span>🤖</span>
                <h3>AI Prediction</h3>
                <p>
                  Predict future passenger demand
                  and crowd levels.
                </p>
              </div>


              <div
                className="module-card"
                onClick={() => setPage("alerts")}
              >
                <span>🔔</span>
                <h3>Alerts</h3>
                <p>
                  Monitor congestion and
                  operational alerts.
                </p>
              </div>


              <div
                className="module-card"
                onClick={() => setPage("analytics")}
              >
                <span>📊</span>
                <h3>Analytics</h3>
                <p>
                  Analyze passenger flow and
                  station performance.
                </p>
              </div>

            </div>

          </section>

        </main>

      )}


      {/* ================= CROWD DASHBOARD ================= */}

   {page === "crowd" && (

  <main className="dashboard-page">

   <section className="crowd-hero">

  <img
    src={metroCrowdImage}
    alt="Metro train"
    className="crowd-hero-bg"
  />

  <div className="crowd-hero-overlay"></div>

  <div className="crowd-hero-content">

    <span className="monitoring-tag">
      ● REAL-TIME MONITORING
    </span>

    <h1>
      Crowd <span>Monitoring</span>
    </h1>

    <p>
      Monitor passenger movement, identify crowded stations,
      and track congestion in real time.
    </p>

  </div>

  <div className="hero-live">
    ● {stationsLoading ? "LOADING" : "LIVE"}
  </div>

</section>

    {stationsError && (
      <p className="data-source-message">
        {stationsError}
      </p>
    )}



    {/* ================================
        SUMMARY CARDS
    ================================= */}

    <div className="summary-grid">

      <div className="summary-card">

        <span>👥</span>

        <div>
          <p>Total Passengers</p>

          <h2>
            {totalPassengers.toLocaleString()}
          </h2>
        </div>

      </div>


      <div className="summary-card">

        <span>🚉</span>

        <div>
          <p>Total Stations</p>

          <h2>
            {stations.length}
          </h2>
        </div>

      </div>


      <div className="summary-card">

        <span>⚠️</span>

        <div>
          <p>High Crowd Stations</p>

          <h2>
            {highCrowdStations}
          </h2>
        </div>

      </div>


      <div className="summary-card">

        <span>🚨</span>

        <div>
          <p>Congested Stations</p>

          <h2>
            {congestedStations}
          </h2>
        </div>

      </div>

    </div>


    {/* ================================
        STATION-WISE CROWD MONITORING
    ================================= */}

    <section className="dashboard-section">

      <div className="section-title">

        <div>

          <h2>
            Station-wise Crowd Monitoring
          </h2>

          <p>
            View passenger activity and congestion
            levels across monitored stations.
          </p>

        </div>

      </div>


      <div className="station-grid">

        {stations.map((station) => (

          <div
            className="station-card"
            key={station.name}
          >

            {/* Station Header */}

            <div className="station-header">

              <div className="station-icon">
                🚉
              </div>

              <div>

                <h3>
                  {station.name}
                </h3>

                <span>
                  Live Station Monitoring
                </span>

              </div>

            </div>


            {/* Passenger Count */}

            <div className="passenger-count">

              <span>
                Total Passengers
              </span>

              <strong>
                {station.passengers}
              </strong>

            </div>


            {/* Inflow / Outflow */}

            <div className="flow-info">

              <div>

                <span className="inflow">
                  ↑ Inflow
                </span>

                <strong>
                  {station.inflow}
                </strong>

              </div>


              <div>

                <span className="outflow">
                  ↓ Outflow
                </span>

                <strong>
                  {station.outflow}
                </strong>

              </div>

            </div>


            {/* Crowd Status */}

            <div className="station-footer">

              <span
                className={`crowd-badge ${station.crowd.toLowerCase()}`}
              >
                {station.crowd} Crowd
              </span>


              <span
                className={`station-status ${
                  station.status === "Congested"
                    ? "congested"
                    : "normal"
                }`}
              >
                {station.status}
              </span>

            </div>

          </div>

        ))}

      </div>

    </section>


    {/* ================================
        PASSENGER FLOW
    ================================= */}

    <section className="dashboard-section">

      <h2>
        Passenger Inflow / Outflow
      </h2>

      <p className="section-description">
        Compare passenger movement across
        monitored stations.
      </p>


      <div className="flow-panel">

        {stations.map((station) => {

          const maxValue = Math.max(
            station.inflow,
            station.outflow
          );

          return (

            <div
              className="flow-row"
              key={station.name}
            >

              <div className="flow-station">
                {station.name}
              </div>


              <div className="bars">

                <div
                  className="bar inflow-bar"
                  style={{
                    width: `${
                      (station.inflow / maxValue) * 100
                    }%`,
                  }}
                >
                  Inflow {station.inflow}
                </div>


                <div
                  className="bar outflow-bar"
                  style={{
                    width: `${
                      (station.outflow / maxValue) * 100
                    }%`,
                  }}
                >
                  Outflow {station.outflow}
                </div>

              </div>

            </div>

          );

        })}

      </div>

    </section>

  </main>

)}


      {/* ================= OTHER MODULES ================= */}

      {page === "schedule" && (
        <ModulePage
          icon="🚆"
          title="Scheduling Management"
          text="Optimize transit schedules and service frequency based on passenger demand."
        />
      )}

      {page === "prediction" && (
        <ModulePage
          icon="🤖"
          title="AI Prediction"
          text="Predict passenger demand and future crowd levels using intelligent analytics."
        />
      )}

      {page === "alerts" && (
        <ModulePage
          icon="🔔"
          title="Alert & Notification"
          text="Monitor overcrowding, delays and important transit operational alerts."
        />
      )}

      {page === "analytics" && (
        <ModulePage
          icon="📊"
          title="Analytics Dashboard"
          text="Analyze passenger traffic, station performance and operational insights."
        />
      )}

    </div>
  );
}


// --------------------------------------------------
// REUSABLE MODULE PAGE
// --------------------------------------------------

function ModulePage({ icon, title, text }) {

  return (

    <main className="module-page">

      <div className="module-placeholder">

        <div className="large-icon">
          {icon}
        </div>

        <h1>{title}</h1>

        <p>{text}</p>

        <span>
          Module ready for development
        </span>

      </div>

    </main>

  );
}

export default App;