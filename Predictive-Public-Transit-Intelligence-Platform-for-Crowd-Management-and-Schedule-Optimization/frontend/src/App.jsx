import { useState } from "react";

function App() {
  const [station, setStation] = useState("");
  const [hour, setHour] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState("");

  const predictRidership = async () => {
    setPrediction(null);
    setError("");

    if (!station || hour === "") {
      setError("Please enter station and hour.");
      return;
    }

    try {
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

      if (data.error) {
        setError(data.error);
      } else {
        setPrediction(data.predicted_ridership);
      }
    } catch (error) {
      setError("Unable to connect to MetroFlow backend.");
    }
  };

  return (
    <div>
      <h1>MetroFlow</h1>

      <h2>Metro Ridership Prediction</h2>

      <div>
        <label>Station</label>
        <br />

        <input
          type="text"
          placeholder="Enter station name"
          value={station}
          onChange={(e) => setStation(e.target.value)}
        />
      </div>

      <br />

      <div>
        <label>Hour</label>
        <br />

        <input
          type="number"
          min="0"
          max="23"
          placeholder="Enter hour (0-23)"
          value={hour}
          onChange={(e) => setHour(e.target.value)}
        />
      </div>

      <br />

      <button onClick={predictRidership}>
        Predict Ridership
      </button>

      {prediction !== null && (
        <h2>
          Predicted Ridership: {prediction}
        </h2>
      )}

      {error && (
        <p>{error}</p>
      )}
    </div>
  );
}

export default App;