
import { useState } from "react";

function App() {
  const [station, setStation] = useState("");
  const [hour, setHour] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [crowdLevel, setCrowdLevel] = useState("");
  const [error, setError] = useState("");

  const handlePredict = async (e) => {
    e.preventDefault();

    setPrediction(null);
    setCrowdLevel("");
    setError("");

    try {
      console.log("Sending request:", {
        station,
        hour: Number(hour),
      });

      const response = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          station: station,
          hour: Number(hour),
        }),
      });

      const data = await response.json();

      console.log("Backend response:", data);

      if (data.error) {
        setError(data.error);
        return;
      }

      setPrediction(data.predicted_ridership);
      setCrowdLevel(data.crowd_level);
    } catch (err) {
      console.error("Error:", err);
      setError("Unable to connect to MetroFlow backend.");
    }
  };

  return (
    <div style={styles.container}>
      <h1>MetroFlow Dashboard</h1>

      <p style={styles.subtitle}>
        AI Metro Crowd Management and Ridership Prediction
      </p>

      <div style={styles.card}>
        <h2>Predict Ridership</h2>

        <form onSubmit={handlePredict}>
          <label>Station</label>

          <input
            type="text"
            value={station}
            onChange={(e) => setStation(e.target.value)}
            placeholder="Enter station"
            required
          />

          <label>Hour</label>

          <input
            type="number"
            min="0"
            max="23"
            value={hour}
            onChange={(e) => setHour(e.target.value)}
            placeholder="Enter hour (0-23)"
            required
          />

          <button type="submit">
            Predict Ridership
          </button>
        </form>
      </div>

      {error && (
        <div style={styles.error}>
          {error}
        </div>
      )}

      {prediction !== null && (
        <div style={styles.resultCard}>
          <h2>Prediction Result</h2>

          <p>
            <strong>Station:</strong> {station}
          </p>

          <p>
            <strong>Hour:</strong> {hour}
          </p>

          <div style={styles.prediction}>
            <span>Predicted Ridership</span>
            <strong>{prediction}</strong>
          </div>

          <div style={styles.crowdBox}>
            <span>Crowd Level</span>

            <strong
              style={{
                ...styles.crowdLevel,
                color:
                  crowdLevel === "HIGH"
                    ? "red"
                    : crowdLevel === "MEDIUM"
                    ? "orange"
                    : "green",
              }}
            >
              {crowdLevel}
            </strong>
          </div>

          {crowdLevel === "HIGH" && (
            <div style={styles.alert}>
              ⚠️ Heavy Crowd Expected
            </div>
          )}

          {crowdLevel === "MEDIUM" && (
            <div style={styles.warning}>
              ⚠️ Moderate Crowd Expected
            </div>
          )}

          {crowdLevel === "LOW" && (
            <div style={styles.success}>
              ✓ Low Crowd Expected
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "700px",
    margin: "40px auto",
    padding: "20px",
    fontFamily: "Arial, sans-serif",
  },

  subtitle: {
    color: "#666",
    marginBottom: "30px",
  },

  card: {
    padding: "25px",
    border: "1px solid #ddd",
    borderRadius: "10px",
    marginBottom: "20px",
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
    color: "red",
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

  alert: {
    marginTop: "20px",
    padding: "15px",
    backgroundColor: "#ffe6e6",
    color: "red",
    borderRadius: "8px",
    fontWeight: "bold",
  },

  warning: {
    marginTop: "20px",
    padding: "15px",
    backgroundColor: "#fff3cd",
    color: "#856404",
    borderRadius: "8px",
    fontWeight: "bold",
  },

  success: {
    marginTop: "20px",
    padding: "15px",
    backgroundColor: "#e6ffe6",
    color: "green",
    borderRadius: "8px",
    fontWeight: "bold",
  },
};

export default App;

