import { useEffect, useState } from "react";
import Login from "./pages/Login";
import CrowdMonitoring from "./pages/CrowdMonitoring";
import Congestion from "./pages/Congestion";

import {
  getStoredUser,
  logout,
  getCrowdSummary,
  getCongestionSummary,
} from "./services/api";

import "./App.css";


function App() {
  const [user, setUser] = useState(getStoredUser());
  const [activePage, setActivePage] = useState("dashboard");

  const [crowdData, setCrowdData] = useState(null);
  const [congestionData, setCongestionData] = useState(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [dataError, setDataError] = useState("");


  useEffect(() => {
    async function loadDashboardData() {
      try {
        setDataLoading(true);
        setDataError("");

        const crowd = await getCrowdSummary();
        setCrowdData(crowd);

        if (
          user.role === "admin" ||
          user.role === "operator"
        ) {
          const congestion = await getCongestionSummary();
          setCongestionData(congestion);
        }
      } catch (error) {
        setDataError(
          error.message || "Unable to load dashboard data."
        );
      } finally {
        setDataLoading(false);
      }
    }

    if (user) {
      loadDashboardData();
    }
  }, [user]);


  function handleLogin(loginData) {
    setUser({
      username: loginData.username,
      role: loginData.role,
    });

    setActivePage("dashboard");
  }


  function handleLogout() {
    logout();
    setUser(null);
    setCrowdData(null);
    setCongestionData(null);
    setActivePage("dashboard");
  }


  function formatNumber(value) {
    return new Intl.NumberFormat("en-US").format(value);
  }


  function formatCompactNumber(value) {
    if (value >= 1000000000) {
      return `${(value / 1000000000).toFixed(2)}B`;
    }

    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(2)}M`;
    }

    if (value >= 1000) {
      return `${(value / 1000).toFixed(2)}K`;
    }

    return formatNumber(value);
  }


  if (!user) {
    return <Login onLogin={handleLogin} />;
  }


  const totalCrowdRecords =
    crowdData?.total_records ?? 0;

  const totalTrafficRecords =
    congestionData?.total_records ?? 0;

  const totalEntries =
    congestionData?.total_entries ?? 0;

  const totalExits =
    congestionData?.total_exits ?? 0;


  const dangerousCount =
    crowdData?.route_status?.find(
      (item) => item.status === "Dangerous"
    )?.count ?? 0;

  const congestedCount =
    crowdData?.route_status?.find(
      (item) => item.status === "Congested"
    )?.count ?? 0;

  const optimalCount =
    crowdData?.route_status?.find(
      (item) => item.status === "Optimal"
    )?.count ?? 0;


  function renderDashboard() {
    return (
      <>
        <header className="topbar">
          <div>
            <p className="eyebrow">
              METRO OPERATIONS CENTER
            </p>
            <h2>Dashboard</h2>
          </div>

          <div className="user-section">
            <div className="notification">
              🔔
            </div>

            <div className="user-avatar">
              {user.username.charAt(0).toUpperCase()}
            </div>

            <div className="user-info">
              <strong>{user.username}</strong>
              <span>{user.role}</span>
            </div>

            <button
              className="logout-button"
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>
        </header>


        <section className="welcome">
          <div>
            <h3>Welcome to AI MetroFlow</h3>
            <p>
              Monitor metro crowd levels, station activity
              and network conditions from one intelligent
              dashboard.
            </p>
          </div>

          <div className="live-badge">
            <span></span>
            LIVE MONITORING
          </div>
        </section>


        {dataError && (
          <div className="data-error">
            ⚠️ {dataError}
          </div>
        )}


        {dataLoading && (
          <div className="data-loading">
            Loading live metro data...
          </div>
        )}


        <section className="stats-grid">

          <div className="stat-card">
            <div className="stat-icon blue">👥</div>

            <div>
              <span>Total Crowd Records</span>

              <strong>
                {dataLoading
                  ? "..."
                  : formatNumber(totalCrowdRecords)}
              </strong>

              <small>Evacuation dataset</small>
            </div>
          </div>


          <div className="stat-card">
            <div className="stat-icon purple">🚉</div>

            <div>
              <span>Traffic Records</span>

              <strong>
                {dataLoading
                  ? "..."
                  : formatCompactNumber(
                      totalTrafficRecords
                    )}
              </strong>

              <small>Subway traffic data</small>
            </div>
          </div>


          <div className="stat-card">
            <div className="stat-icon green">📥</div>

            <div>
              <span>Total Entries</span>

              <strong>
                {dataLoading
                  ? "..."
                  : formatCompactNumber(totalEntries)}
              </strong>

              <small>Recorded entries</small>
            </div>
          </div>


          <div className="stat-card">
            <div className="stat-icon orange">📤</div>

            <div>
              <span>Total Exits</span>

              <strong>
                {dataLoading
                  ? "..."
                  : formatCompactNumber(totalExits)}
              </strong>

              <small>Recorded exits</small>
            </div>
          </div>

        </section>


        <section className="dashboard-grid">

          <div className="panel">

            <div className="panel-header">
              <div>
                <h3>Crowd Route Status</h3>
                <p>
                  Current distribution from monitoring data
                </p>
              </div>

              <span className="panel-badge">
                {totalCrowdRecords} records
              </span>
            </div>


            <div className="route-list">

              <div className="route-row">
                <div className="route-label">
                  <span className="route-dot danger"></span>
                  Dangerous
                </div>

                <strong>{dangerousCount}</strong>
              </div>

              <div className="progress">
                <div
                  className="progress-danger"
                  style={{
                    width:
                      totalCrowdRecords
                        ? `${(dangerousCount / totalCrowdRecords) * 100}%`
                        : "0%",
                  }}
                ></div>
              </div>


              <div className="route-row">
                <div className="route-label">
                  <span className="route-dot warning"></span>
                  Congested
                </div>

                <strong>{congestedCount}</strong>
              </div>

              <div className="progress">
                <div
                  className="progress-warning"
                  style={{
                    width:
                      totalCrowdRecords
                        ? `${(congestedCount / totalCrowdRecords) * 100}%`
                        : "0%",
                  }}
                ></div>
              </div>


              <div className="route-row">
                <div className="route-label">
                  <span className="route-dot success"></span>
                  Optimal
                </div>

                <strong>{optimalCount}</strong>
              </div>

              <div className="progress">
                <div
                  className="progress-success"
                  style={{
                    width:
                      totalCrowdRecords
                        ? `${(optimalCount / totalCrowdRecords) * 100}%`
                        : "0%",
                  }}
                ></div>
              </div>

            </div>
          </div>


          <div className="panel">

            <div className="panel-header">
              <div>
                <h3>System Overview</h3>
                <p>AI MetroFlow platform status</p>
              </div>
            </div>


            <div className="overview-list">

              <div className="overview-item">
                <span>FastAPI Backend</span>
                <strong className="online">
                  ● Online
                </strong>
              </div>

              <div className="overview-item">
                <span>PostgreSQL Database</span>
                <strong className="online">
                  ● Connected
                </strong>
              </div>

              <div className="overview-item">
                <span>Authentication</span>
                <strong className="online">
                  ● Active
                </strong>
              </div>

              <div className="overview-item">
                <span>Role Security</span>
                <strong className="online">
                  ● Active
                </strong>
              </div>

            </div>
          </div>

        </section>


        <section className="panel station-panel">

          <div className="panel-header">
            <div>
              <h3>Top Active Stations</h3>
              <p>
                Stations ranked by combined entries and exits
              </p>
            </div>
          </div>


          <div className="station-table">

            <div className="table-header">
              <span>#</span>
              <span>Station</span>
              <span>Entries</span>
              <span>Exits</span>
              <span>Total Activity</span>
            </div>


            {congestionData?.top_congested_stations
              ?.slice(0, 4)
              .map((station, index) => (

                <div
                  className="table-row"
                  key={station.station}
                >
                  <span>
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <strong>{station.station}</strong>

                  <span>
                    {formatCompactNumber(station.entries)}
                  </span>

                  <span>
                    {formatCompactNumber(station.exits)}
                  </span>

                  <strong>
                    {formatCompactNumber(
                      station.total_activity
                    )}
                  </strong>
                </div>

              ))}

          </div>
        </section>


        <footer>
          <span>AI MetroFlow v1.0</span>
          <span>
            Metro Crowd Management & Scheduling Platform
          </span>
        </footer>
      </>
    );
  }


  return (
    <div className="app">

      <aside className="sidebar">

        <div className="logo">
          <span className="logo-icon">🚇</span>

          <div>
            <h1>AI MetroFlow</h1>
            <p>Metro Intelligence</p>
          </div>
        </div>


        <nav>

          <button
            type="button"
            className={
              activePage === "dashboard"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() => setActivePage("dashboard")}
          >
            <span>▦</span>
            Dashboard
          </button>


          <button
            type="button"
            className={
              activePage === "crowd"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() => setActivePage("crowd")}
          >
            <span>👥</span>
            Crowd Monitoring
          </button>


          <button
            type="button"
            className={
              activePage === "congestion"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() => setActivePage("congestion")}
          >
            <span>📊</span>
            Congestion
          </button>


          <button
            type="button"
            className={
              activePage === "alerts"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() => setActivePage("alerts")}
          >
            <span>🚨</span>
            Alerts
          </button>


          <button
            type="button"
            className={
              activePage === "analytics"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() => setActivePage("analytics")}
          >
            <span>📈</span>
            Analytics
          </button>

        </nav>


        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot"></span>

            <div>
              <strong>System Online</strong>
              <small>All services operational</small>
            </div>
          </div>
        </div>

      </aside>


      <main className="main-content">

        {activePage === "dashboard" && renderDashboard()}


        {activePage === "crowd" && (
          <CrowdMonitoring />
        )}


        {activePage === "congestion" && (
          <Congestion />
        )}


        {activePage === "alerts" && (
          <div className="page-content">

            <div className="page-heading">
              <div>
                <p className="eyebrow">
                  METRO OPERATIONS CENTER
                </p>

                <h2>Alerts</h2>

                <p>
                  Overcrowding, delay and emergency alerts.
                </p>
              </div>

              <div className="live-badge">
                <span></span>
                PLANNED
              </div>
            </div>


            <div className="panel coming-soon-panel">
              <div className="coming-soon-icon">
                🚨
              </div>

              <h3>Alerts Module</h3>

              <p>
                Alert management will be implemented in
                the upcoming milestone.
              </p>
            </div>

          </div>
        )}


        {activePage === "analytics" && (
          <div className="page-content">

            <div className="page-heading">
              <div>
                <p className="eyebrow">
                  AI METROFLOW INTELLIGENCE
                </p>

                <h2>Analytics</h2>

                <p>
                  AI-powered metro traffic analytics and
                  recommendations.
                </p>
              </div>

              <div className="live-badge">
                <span></span>
                PLANNED
              </div>
            </div>


            <div className="panel coming-soon-panel">
              <div className="coming-soon-icon">
                📈
              </div>

              <h3>Analytics Module</h3>

              <p>
                Advanced analytics will be implemented in
                the upcoming milestone.
              </p>
            </div>

          </div>
        )}

      </main>

    </div>
  );
}
export default App;