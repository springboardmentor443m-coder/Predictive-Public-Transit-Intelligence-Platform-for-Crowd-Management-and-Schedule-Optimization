import { useEffect, useState } from "react";
import { getCongestionSummary } from "../services/api";

function Congestion() {
  const [congestionData, setCongestionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadCongestionData() {
      try {
        setLoading(true);
        setError("");

        const data = await getCongestionSummary();
        setCongestionData(data);
      } catch (err) {
        setError(err.message || "Unable to load congestion data.");
      } finally {
        setLoading(false);
      }
    }

    loadCongestionData();
  }, []);

  const totalRecords = congestionData?.total_records ?? 0;
  const totalEntries = congestionData?.total_entries ?? 0;
  const totalExits = congestionData?.total_exits ?? 0;

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

    return value.toLocaleString();
  }

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <p className="eyebrow">NETWORK CONGESTION INTELLIGENCE</p>
          <h2>Congestion Tracking</h2>
          <p>
            Analyze station activity using recorded metro entry and
            exit data.
          </p>
        </div>

        <div className="live-badge">
          <span></span>
          LIVE DATA
        </div>
      </div>

      {loading && (
        <div className="data-loading">
          Loading congestion data...
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
              <div className="stat-icon purple">🚉</div>
              <div>
                <span>Total Traffic Records</span>
                <strong>{formatCompactNumber(totalRecords)}</strong>
                <small>Subway traffic dataset</small>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon blue">📥</div>
              <div>
                <span>Total Entries</span>
                <strong>{formatCompactNumber(totalEntries)}</strong>
                <small>Recorded station entries</small>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon green">📤</div>
              <div>
                <span>Total Exits</span>
                <strong>{formatCompactNumber(totalExits)}</strong>
                <small>Recorded station exits</small>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon orange">📊</div>
              <div>
                <span>Stations Analyzed</span>
                <strong>
                  {congestionData?.top_congested_stations?.length ?? 0}
                </strong>
                <small>Top active stations shown</small>
              </div>
            </div>
          </section>

          <section className="panel station-panel">
            <div className="panel-header">
              <div>
                <h3>Top Active Stations</h3>
                <p>
                  Stations ranked by combined recorded entries and
                  exits
                </p>
              </div>

              <span className="panel-badge">
                Top 10
              </span>
            </div>

            <div className="station-table">
              <div className="table-header">
                <span>#</span>
                <span>Station</span>
                <span>Entries</span>
                <span>Exits</span>
                <span>Total Activity</span>
              </div>

              {congestionData?.top_congested_stations?.map(
                (station, index) => (
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
                )
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default Congestion;