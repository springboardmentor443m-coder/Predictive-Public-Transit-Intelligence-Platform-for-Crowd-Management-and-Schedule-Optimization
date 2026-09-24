import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ComponentType,
  type ReactNode,
} from "react";
import api from "./api";
import type { User } from "./types";

const TOKEN_KEY = "metroflow_token";
const USER_KEY = "metroflow_user";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<User>;
  hasRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readSession(): { token: string | null; user: string | null } {
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
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
      .get<User>("/auth/me")
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

  const refreshUser = useCallback(async (): Promise<User> => {
    const res = await api.get<User>("/auth/me");
    sessionStorage.setItem(USER_KEY, JSON.stringify(res.data));
    setUser(res.data);
    return res.data;
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<User> => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const res = await api.post<{ access_token: string }>("/auth/login", form.toString(), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    sessionStorage.setItem(TOKEN_KEY, res.data.access_token);
    const me = await api.get<User>("/auth/me");
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
    (...roles: string[]) => !!(user && roles.includes(user.role)),
    [user]
  );

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function withAuth<P extends object>(Component: ComponentType<P>) {
  return function Protected(props: P) {
    const auth = useAuth();
    const { user, loading } = auth || { user: null, loading: true };
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