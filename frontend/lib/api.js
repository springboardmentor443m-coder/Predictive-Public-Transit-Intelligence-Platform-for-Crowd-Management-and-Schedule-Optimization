import axios from "axios";

// Empty/unset NEXT_PUBLIC_API_URL -> same-origin requests (proxied by
// next.config.js rewrites to BACKEND_INTERNAL_URL in container deployments).
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = sessionStorage.getItem("metroflow_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.status === 401 && typeof window !== "undefined") {
      sessionStorage.removeItem("metroflow_token");
      sessionStorage.removeItem("metroflow_user");
      localStorage.removeItem("metroflow_token");
      localStorage.removeItem("metroflow_user");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export default api;
