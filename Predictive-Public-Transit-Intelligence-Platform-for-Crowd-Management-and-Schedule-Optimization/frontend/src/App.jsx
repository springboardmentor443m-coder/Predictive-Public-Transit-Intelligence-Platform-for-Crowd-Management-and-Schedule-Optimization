import { useEffect, useState } from "react";

function App() {
  // =====================================================
  // LOGIN
  // =====================================================

  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");

  // =====================================================
  // PREDICTION STATES
  // =====================================================

  const [station, setStation] = useState("");
  const [hour, setHour] = useState("");

  const [prediction, setPrediction] = useState(null);
  const [crowdLevel, setCrowdLevel] = useState("");

  // Crowd Alert
  const [alert, setAlert] = useState("");
  const [recommendedAction, setRecommendedAction] = useState("");

  const [error, setError] = useState("");

  // =====================================================
  // ANALYTICS STATES
  // =====================================================

  const [analytics, setAnalytics] = useState(null);
  const [analyticsError, setAnalyticsError] = useState("");
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);

  // =====================================================
  // FETCH ANALYTICS
  // =====================================================

  useEffect(() => {
    if (!isLoggedIn) {
      return;
    }

    fetch("http://127.0.0.1:8000/analytics")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Analytics API error");
        }

        return response.json();
      })
      .then((data) => {
        console.log("Analytics response:", data);

        setAnalytics(data);
        setLoadingAnalytics(false);
      })
      .catch((err) => {
        console.error("Analytics error:", err);

        setAnalyticsError("Unable to load analytics.");
        setLoadingAnalytics(false);
      });
  }, [isLoggedIn]);

  // =====================================================
  // LOGIN FUNCTION
  // =====================================================

  const handleLogin = (e) => {
    e.preventDefault();

    setLoginError("");

    if (!email || !password) {
      setLoginError("Please enter email and password.");
      return;
    }

    // Temporary frontend login
    // We will connect this to FastAPI later.

    setIsLoggedIn(true);
  };

  // =====================================================
  // LOGOUT FUNCTION
  // =====================================================

  const handleLogout = () => {
    setIsLoggedIn(false);

    setEmail("");
    setPassword("");

    setStation("");
    setHour("");

    setPrediction(null);
    setCrowdLevel("");

    setAlert("");
    setRecommendedAction("");

    setError("");
  };

  // =====================================================
  // PREDICTION FUNCTION
  // =====================================================

  const handlePredict = async (e) => {
    e.preventDefault();

    setPrediction(null);
    setCrowdLevel("");

    setAlert("");
    setRecommendedAction("");

    setError("");

    try {
      console.log("Sending request:", {
        station,
        hour: Number(hour),
      });

      const response = await fetch(
        "http://127.0.0.1:8000/predict",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            station: station,
            hour: Number(hour),
          }),
        }
      );

      const data = await response.json();

      console.log("Backend response:", data);

      if (data.error) {
        setError(data.error);
        return;
      }

      setPrediction(data.predicted_ridership);

      setCrowdLevel(data.crowd_level);

      setAlert(data.alert);

      setRecommendedAction(
        data.recommended_action
      );
    } catch (err) {
      console.error("Prediction error:", err);

      setError(
        "Unable to connect to MetroFlow backend."
      );
    }
  };

  // =====================================================
  // MAX HOURLY RIDERSHIP
  // =====================================================

  const maxHourlyRidership =
    analytics &&
    analytics.hourly_ridership.length > 0
      ? Math.max(
          ...analytics.hourly_ridership.map(
            (item) => item.Ridership
          )
        )
      : 0;

  // =====================================================
  // LOGIN PAGE
  // =====================================================

  if (!isLoggedIn) {
    return (
      <div style={styles.loginContainer}>

        <div style={styles.loginCard}>

          <div style={styles.loginIcon}>
            🚇
          </div>

          <h1 style={styles.loginTitle}>
            MetroFlow
          </h1>

          <p style={styles.loginSubtitle}>
            AI Metro Crowd Management System
          </p>

          <h2>
            Login
          </h2>

          <form onSubmit={handleLogin}>

            <input
              type="email"
              placeholder="Enter email"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              style={styles.loginInput}
            />

            <input
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              style={styles.loginInput}
            />

            {loginError && (
              <div style={styles.loginError}>
                {loginError}
              </div>
            )}

            <button
              type="submit"
              style={styles.loginButton}
            >
              Login
            </button>

          </form>

          <p style={styles.loginFooter}>
            MetroFlow • Smart Metro Management
          </p>

        </div>

      </div>
    );
  }

  // =====================================================
  // DASHBOARD
  // =====================================================

  return (
    <div style={styles.container}>

      {/* =================================================
          HEADER
      ================================================= */}

      <div style={styles.header}>

        <div>

          <h1>
            MetroFlow Dashboard
          </h1>

          <p style={styles.subtitle}>
            AI Metro Crowd Management and
            Ridership Prediction
          </p>

        </div>

        <button
          onClick={handleLogout}
          style={styles.logoutButton}
        >
          Logout
        </button>

      </div>

      {/* =================================================
          PREDICTION SECTION
      ================================================= */}

      <div style={styles.card}>

        <h2>
          Predict Ridership
        </h2>

        <form onSubmit={handlePredict}>

          <label style={styles.label}>
            Station
          </label>

          <input
            type="text"
            value={station}
            onChange={(e) =>
              setStation(e.target.value)
            }
            placeholder="Enter station"
            required
            style={styles.input}
          />

          <label style={styles.label}>
            Hour
          </label>

          <input
            type="number"
            min="0"
            max="23"
            value={hour}
            onChange={(e) =>
              setHour(e.target.value)
            }
            placeholder="Enter hour (0-23)"
            required
            style={styles.input}
          />

          <button
            type="submit"
            style={styles.button}
          >
            Predict Ridership
          </button>

        </form>

      </div>

      {/* =================================================
          ERROR
      ================================================= */}

      {error && (
        <div style={styles.error}>
          {error}
        </div>
      )}

      {/* =================================================
          PREDICTION RESULT
      ================================================= */}

      {prediction !== null && (

        <div style={styles.resultCard}>

          <h2>
            Prediction Result
          </h2>

          <p>
            <strong>Station:</strong>{" "}
            {station}
          </p>

          <p>
            <strong>Hour:</strong>{" "}
            {hour}:00
          </p>

          {/* RIDERSHIP */}

          <div style={styles.prediction}>

            <span>
              Predicted Ridership
            </span>

            <strong>
              {prediction}
            </strong>

          </div>

          {/* CROWD LEVEL */}

          <div style={styles.crowdBox}>

            <span>
              Crowd Level
            </span>

            <strong
              style={{
                ...styles.crowdLevel,

                color:
                  crowdLevel === "HIGH"
                    ? "#ff4444"
                    : crowdLevel === "MEDIUM"
                    ? "#ff9800"
                    : "#22c55e",
              }}
            >
              {crowdLevel}
            </strong>

          </div>

          {/* =================================================
              CROWD ALERT
          ================================================= */}

          <div
            style={{
              ...styles.crowdAlert,

              borderColor:
                crowdLevel === "HIGH"
                  ? "#ff4444"
                  : crowdLevel === "MEDIUM"
                  ? "#ff9800"
                  : "#22c55e",

              backgroundColor:
                crowdLevel === "HIGH"
                  ? "#3b1616"
                  : crowdLevel === "MEDIUM"
                  ? "#3b2b12"
                  : "#12351f",
            }}
          >

            <h3>
              {crowdLevel === "HIGH"
                ? "🚨 Crowd Alert"
                : crowdLevel === "MEDIUM"
                ? "⚠️ Crowd Alert"
                : "✅ Crowd Status"}
            </h3>

            <p>
              <strong>
                {alert}
              </strong>
            </p>

            <p>
              <strong>
                Recommended Action:
              </strong>
            </p>

            <p>
              {recommendedAction}
            </p>

          </div>

        </div>
      )}

      {/* =================================================
          ANALYTICS
      ================================================= */}

      <div style={styles.analyticsSection}>

        <h2>
          Metro Analytics
        </h2>

        <p style={styles.subtitle}>
          Ridership trends and station-level
          analysis
        </p>

        {/* LOADING */}

        {loadingAnalytics && (
          <div style={styles.loading}>
            Loading analytics...
          </div>
        )}

        {/* ERROR */}

        {analyticsError && (
          <div style={styles.error}>
            {analyticsError}
          </div>
        )}

        {/* ANALYTICS DATA */}

        {analytics && (

          <>

            {/* =================================================
                PEAK HOUR
            ================================================= */}

            <div style={styles.peakCard}>

              <h3>
                Peak Hour
              </h3>

              <div style={styles.peakValue}>
                {analytics.peak_hour}:00
              </div>

              <p>
                Average Ridership:{" "}
                <strong>
                  {analytics.peak_ridership}
                </strong>
              </p>

            </div>

            {/* =================================================
                HOURLY RIDERSHIP
            ================================================= */}

            <div style={styles.chartCard}>

              <h3>
                Hourly Ridership Trend
              </h3>

              <div style={styles.chart}>

                {analytics.hourly_ridership.map(
                  (item) => {

                    const barHeight =
                      maxHourlyRidership > 0
                        ? (item.Ridership /
                            maxHourlyRidership) *
                          200
                        : 0;

                    return (
                      <div
                        key={item.Hour}
                        style={
                          styles.barContainer
                        }
                      >

                        <div
                          style={{
                            ...styles.bar,
                            height:
                              `${barHeight}px`,
                          }}
                          title={
                            `Hour ${item.Hour}: ` +
                            `${item.Ridership}`
                          }
                        />

                        <span
                          style={
                            styles.hourLabel
                          }
                        >
                          {item.Hour}
                        </span>

                      </div>
                    );
                  }
                )}

              </div>

              <p style={styles.chartLabel}>
                Hour of Day
              </p>

            </div>

            {/* =================================================
                STATION RIDERSHIP
            ================================================= */}

            <div style={styles.chartCard}>

              <h3>
                Station-wise Ridership
              </h3>

              <div style={styles.stationList}>

                {analytics.station_ridership
                  .slice(0, 10)
                  .map(
                    (item, index) => (

                      <div
                        key={item.Station}
                        style={
                          styles.stationRow
                        }
                      >

                        <span>
                          {index + 1}.{" "}
                          {item.Station}
                        </span>

                        <strong>
                          {item.Ridership}
                        </strong>

                      </div>

                    )
                  )}

              </div>

              <p style={styles.chartLabel}>
                Top 10 stations by average
                ridership
              </p>

            </div>

          </>
        )}

      </div>

    </div>
  );
}


// =====================================================
// STYLES
// =====================================================

const styles = {

  // ===================================================
  // LOGIN
  // ===================================================

  loginContainer: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#111827",
    padding: "20px",
  },

  loginCard: {
    width: "380px",
    padding: "35px",
    backgroundColor: "#1f2937",
    borderRadius: "15px",
    boxShadow:
      "0 10px 30px rgba(0, 0, 0, 0.4)",
    textAlign: "center",
    boxSizing: "border-box",
  },

  loginIcon: {
    fontSize: "50px",
    marginBottom: "10px",
  },

  loginTitle: {
    marginBottom: "5px",
  },

  loginSubtitle: {
    color: "#9ca3af",
    marginBottom: "30px",
  },

  loginInput: {
    width: "100%",
    padding: "13px",
    marginTop: "12px",
    boxSizing: "border-box",
    border: "1px solid #4b5563",
    borderRadius: "7px",
    backgroundColor: "#111827",
    color: "white",
    fontSize: "16px",
  },

  loginButton: {
    width: "100%",
    marginTop: "20px",
    padding: "13px",
    border: "none",
    borderRadius: "7px",
    backgroundColor: "#2196f3",
    color: "white",
    fontSize: "16px",
    cursor: "pointer",
  },

  loginError: {
    marginTop: "15px",
    padding: "10px",
    backgroundColor: "#3b1616",
    color: "#ff6666",
    borderRadius: "6px",
  },

  loginFooter: {
    marginTop: "25px",
    color: "#6b7280",
    fontSize: "13px",
  },

  // ===================================================
  // DASHBOARD
  // ===================================================

  container: {
    maxWidth: "900px",
    margin: "40px auto",
    padding: "20px",
    fontFamily: "Arial, sans-serif",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "20px",
  },

  subtitle: {
    color: "#888",
    marginBottom: "30px",
  },

  logoutButton: {
    padding: "10px 18px",
    border: "none",
    borderRadius: "6px",
    backgroundColor: "#dc3545",
    color: "white",
    fontSize: "14px",
    cursor: "pointer",
  },

  card: {
    padding: "25px",
    border: "1px solid #ddd",
    borderRadius: "10px",
    marginBottom: "20px",
  },

  label: {
    display: "block",
    marginTop: "15px",
    marginBottom: "8px",
    fontWeight: "bold",
  },

  input: {
    width: "100%",
    padding: "12px",
    boxSizing: "border-box",
    border: "1px solid #ccc",
    borderRadius: "6px",
    fontSize: "16px",
  },

  button: {
    marginTop: "20px",
    padding: "12px 20px",
    border: "none",
    borderRadius: "6px",
    backgroundColor: "#2196f3",
    color: "white",
    fontSize: "16px",
    cursor: "pointer",
  },

  resultCard: {
    padding: "25px",
    border: "1px solid #ddd",
    borderRadius: "10px",
    marginTop: "20px",
  },

  error: {
    padding: "15px",
    backgroundColor: "#ffe6e6",
    color: "#ff4444",
    borderRadius: "8px",
    marginTop: "20px",
  },

  loading: {
    padding: "15px",
    backgroundColor: "#f5f5f5",
    borderRadius: "8px",
    marginTop: "20px",
  },

  prediction: {
    marginTop: "20px",
    padding: "20px",
    backgroundColor: "#f5f5f5",
    borderRadius: "8px",
    display: "flex",
    justifyContent: "space-between",
    fontSize: "20px",
  },

  crowdBox: {
    marginTop: "15px",
    padding: "20px",
    backgroundColor: "#f5f5f5",
    borderRadius: "8px",
    display: "flex",
    justifyContent: "space-between",
    fontSize: "20px",
  },

  crowdLevel: {
    fontSize: "24px",
  },

  // ===================================================
  // CROWD ALERT
  // ===================================================

  crowdAlert: {
    marginTop: "20px",
    padding: "20px",
    border: "2px solid",
    borderRadius: "10px",
    lineHeight: "1.6",
  },

  // ===================================================
  // ANALYTICS
  // ===================================================

  analyticsSection: {
    marginTop: "40px",
  },

  peakCard: {
    padding: "25px",
    border: "1px solid #ddd",
    borderRadius: "10px",
    marginBottom: "20px",
    textAlign: "center",
  },

  peakValue: {
    fontSize: "40px",
    fontWeight: "bold",
    margin: "15px 0",
  },

  chartCard: {
    padding: "25px",
    border: "1px solid #ddd",
    borderRadius: "10px",
    marginBottom: "20px",
  },

  chart: {
    height: "240px",
    display: "flex",
    alignItems: "flex-end",
    gap: "8px",
    padding: "20px 10px 0",
    borderBottom: "1px solid #ccc",
    overflowX: "auto",
  },

  barContainer: {
    minWidth: "25px",
    height: "220px",
    display: "flex",
    flexDirection: "column",
    justifyContent: "flex-end",
    alignItems: "center",
  },

  bar: {
    width: "20px",
    backgroundColor: "#2196f3",
    borderRadius: "4px 4px 0 0",
    minHeight: "2px",
  },

  hourLabel: {
    marginTop: "8px",
    fontSize: "12px",
  },

  chartLabel: {
    textAlign: "center",
    color: "#888",
    marginTop: "15px",
  },

  stationList: {
    marginTop: "15px",
  },

  stationRow: {
    display: "flex",
    justifyContent: "space-between",
    padding: "12px",
    borderBottom: "1px solid #eee",
  },
};

export default App;