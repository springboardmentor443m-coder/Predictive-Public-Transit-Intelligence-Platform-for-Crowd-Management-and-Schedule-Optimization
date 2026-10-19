import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Brain, Lock, User, LogIn } from "lucide-react";
import { loginUser } from "../services/api";

function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      await loginUser(username, password);
      navigate("/");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Login failed. Please check your username and password."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page">
      <div className="login-container">

        <div className="login-brand">
          <div className="login-logo">
            <Brain size={30} />
          </div>

          <div>
            <h1>AI MetroFlow</h1>
            <p>Predictive Public Transit Intelligence</p>
          </div>
        </div>

        <div className="login-card">

          <div className="login-heading">
            <span className="eyebrow">SECURE ACCESS</span>
            <h2>Welcome back</h2>
            <p>
              Sign in to access the MetroFlow operations intelligence
              dashboard.
            </p>
          </div>

          <form onSubmit={handleLogin}>

            <div className="login-field">
              <label>Username</label>

              <div className="login-input">
                <User size={18} />

                <input
                  type="text"
                  value={username}
                  onChange={(event) =>
                    setUsername(event.target.value)
                  }
                  placeholder="Enter username"
                  required
                />
              </div>
            </div>

            <div className="login-field">
              <label>Password</label>

              <div className="login-input">
                <Lock size={18} />

                <input
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter password"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="login-error">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="login-button"
              disabled={loading}
            >
              {loading ? (
                "Authenticating..."
              ) : (
                <>
                  <LogIn size={18} />
                  Sign In
                </>
              )}
            </button>

          </form>
        </div>

        <div className="login-footer">
          AI MetroFlow • BMRCL Intelligence Platform
        </div>

      </div>
    </main>
  );
}

export default Login;