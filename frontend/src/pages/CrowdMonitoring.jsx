import { useEffect, useState } from "react";
import { getCrowdSummary } from "../services/api";

function CrowdMonitoring() {
  const [crowdData, setCrowdData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadCrowdData() {
      try {
        setLoading(true);
        setError("");

        const data = await getCrowdSummary();
        setCrowdData(data);
      } catch (err) {
        setError(err.message || "Unable to load crowd data.");
      } finally {
        setLoading(false);
      }
    }

    loadCrowdData();
  }, []);

  const totalRecords = crowdData?.total_records ?? 0;

  const dangerous =
    crowdData?.route_status?.find(
      (item) => item.status === "Dangerous"
    )?.count ?? 0;

  const congested =
    crowdData?.route_status?.find(
      (item) => item.status === "Congested"
    )?.count ?? 0;

  const optimal =
    crowdData?.route_status?.find(
      (item) => item.status === "Optimal"
    )?.count ?? 0;

  function percentage(value) {
    if (!totalRecords) return 0;
    return ((value / totalRecords) * 100).toFixed(1);
  }

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <p className="eyebrow">REAL-TIME CROWD INTELLIGENCE</p>
          <h2>Crowd Monitoring</h2>
          <p>
            Monitor crowd conditions and route safety using metro
            monitoring data.
          </p>
        </div>

        <div className="live-badge">
          <span></span>
          LIVE DATA
        </div>
      </div>

      {loading && (
        <div className="data-loading">
          Loading crowd monitoring data...
        </div>
      )}

      {error && (
        <div className="data-error">
          ⚠️ {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <section className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon blue">👥</div>
              <div>
                <span>Total Monitoring Records</span>
                <strong>{totalRecords.toLocaleString()}</strong>
                <small>Crowd evacuation dataset</small>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon orange">⚠️</div>
              <div>
                <span>Dangerous Routes</span>
                <strong>{dangerous}</strong>
                <small>{percentage(dangerous)}% of records</small>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon purple">🚧</div>
              <div>
                <span>Congested Routes</span>
                <strong>{congested}</strong>
                <small>{percentage(congested)}% of records</small>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon green">✓</div>
              <div>
                <span>Optimal Routes</span>
                <strong>{optimal}</strong>
                <small>{percentage(optimal)}% of records</small>
              </div>
            </div>
          </section>

          <section className="dashboard-grid">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>Route Safety Distribution</h3>
                  <p>Distribution of monitored route conditions</p>
                </div>
              </div>

              <div className="route-list">
                <div className="route-row">
                  <div className="route-label">
                    <span className="route-dot danger"></span>
                    Dangerous
                  </div>
                  <strong>{dangerous}</strong>
                </div>

                <div className="progress">
                  <div
                    className="progress-danger"
                    style={{
                      width: `${percentage(dangerous)}%`,
                    }}
                  ></div>
                </div>

                <div className="route-row">
                  <div className="route-label">
                    <span className="route-dot warning"></span>
                    Congested
                  </div>
                  <strong>{congested}</strong>
                </div>

                <div className="progress">
                  <div
                    className="progress-warning"
                    style={{
                      width: `${percentage(congested)}%`,
                    }}
                  ></div>
                </div>

                <div className="route-row">
                  <div className="route-label">
                    <span className="route-dot success"></span>
                    Optimal
                  </div>
                  <strong>{optimal}</strong>
                </div>

                <div className="progress">
                  <div
                    className="progress-success"
                    style={{
                      width: `${percentage(optimal)}%`,
                    }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>Monitoring Scenarios</h3>
                  <p>Recorded crowd-related scenarios</p>
                </div>
              </div>

              <div className="overview-list">
                {crowdData?.scenarios?.map((item) => (
                  <div
                    className="overview-item"
                    key={item.scenario}
                  >
                    <span>{item.scenario}</span>
                    <strong>{item.count}</strong>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default CrowdMonitoring;