import { useState } from "react";
import "./App.css";

function App() {
  const [role, setRole] = useState("Operator");

  const handleLogin = (e) => {
    e.preventDefault();
    alert(`Login clicked as ${role}`);
  };

  return (
    <div className="app">
      <div className="login-container">
        <div className="brand-section">
          <h1>🚆 MetroFlow</h1>
          <p>Predictive Public Transit Intelligence Platform</p>

          <div className="info-box">
            <h2>Smart Transit. Better Decisions.</h2>
            <p>
              Monitor passenger crowds, detect congestion, and support
              intelligent public transit management.
            </p>
          </div>
        </div>

        <div className="login-section">
          <h2>Welcome Back</h2>
          <p className="subtitle">Login to access MetroFlow</p>

          <form onSubmit={handleLogin}>
            <label>Email</label>
            <input
              type="email"
              placeholder="Enter your email"
              required
            />

            <label>Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              required
            />

            <label>Login Role</label>

            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option>Operator</option>
              <option>Admin</option>
            </select>

            <button type="submit">Login</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;