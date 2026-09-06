import { useState } from "react";
import { login } from "../services/api";

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const user = await login(username, password);
      onLogin(user);
    } catch (err) {
      setError(err.message || "Unable to login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">🚇</div>

        <p className="login-label">METRO INTELLIGENCE PLATFORM</p>

        <h1>AI MetroFlow</h1>

        <p className="login-description">
          Sign in to access the metro crowd management dashboard.
        </p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="username">Username</label>

          <input
            id="username"
            type="text"
            placeholder="Enter your username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />

          <label htmlFor="password">Password</label>

          <input
            id="password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          {error && <div className="login-error">{error}</div>}

          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="login-footer">
          <span className="login-status-dot"></span>
          Secure JWT Authentication
        </div>
      </div>
    </div>
  );
}

export default Login;