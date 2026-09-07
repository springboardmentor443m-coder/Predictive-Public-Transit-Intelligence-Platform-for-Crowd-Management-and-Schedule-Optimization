import { createContext, useCallback, useContext, useEffect, useState } from "react";
import api from "./api";

const AuthContext = createContext(null);

const TOKEN_KEY = "metroflow_token";
const USER_KEY = "metroflow_user";

function readSession() {
  if (typeof window === "undefined") return { token: null, user: null };
  return {
    token: sessionStorage.getItem(TOKEN_KEY),
    user: sessionStorage.getItem(USER_KEY),
  };
}

function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
  // Purge legacy persistent sessions from older builds.
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const { token, user: cached } = readSession();
    if (!token) {
      clearSession();
      setLoading(false);
      return;
    }
    if (cached) {
      try {
        setUser(JSON.parse(cached));
      } catch {}
    }
    api
      .get("/auth/me")
      .then((res) => {
        setUser(res.data);
        sessionStorage.setItem(USER_KEY, JSON.stringify(res.data));
      })
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const refreshUser = useCallback(async () => {
    const res = await api.get("/auth/me");
    sessionStorage.setItem(USER_KEY, JSON.stringify(res.data));
    setUser(res.data);
    return res.data;
  }, []);

  const login = useCallback(async (email, password) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const res = await api.post("/auth/login", form.toString(), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    sessionStorage.setItem(TOKEN_KEY, res.data.access_token);
    const me = await api.get("/auth/me");
    sessionStorage.setItem(USER_KEY, JSON.stringify(me.data));
    setUser(me.data);
    return me.data;
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
    window.location.href = "/login";
  }, []);

  const hasRole = useCallback(
    (...roles) => user && roles.includes(user.role),
    [user]
  );

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function withAuth(Component) {
  return function Protected(props) {
    const { user, loading } = useAuth();
    useEffect(() => {
      if (!loading && !user) window.location.href = "/login";
    }, [loading, user]);
    if (loading || !user) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-100">
          <div className="animate-pulse text-slate-500 font-medium">Loading MetroFlow…</div>
        </div>
      );
    }
    return <Component {...props} />;
  };
}
