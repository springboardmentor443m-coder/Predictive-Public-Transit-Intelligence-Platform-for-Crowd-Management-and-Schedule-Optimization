const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
  const token = localStorage.getItem("metroflow_token");

  const headers = {
    Accept: "application/json",
    ...options.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || `Request failed with status ${response.status}`);
  }

  return data;
}

export async function login(username, password) {
  const body = new URLSearchParams();

  body.append("username", username);
  body.append("password", password);

  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Accept: "application/json",
    },
    body,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Login failed");
  }

  localStorage.setItem("metroflow_token", data.access_token);
  localStorage.setItem(
    "metroflow_user",
    JSON.stringify({
      username: data.username,
      role: data.role,
    })
  );

  return data;
}

export function logout() {
  localStorage.removeItem("metroflow_token");
  localStorage.removeItem("metroflow_user");
}

export async function getCurrentUser() {
  return request("/api/auth/me");
}

export async function getCrowdSummary() {
  return request("/api/crowd/summary");
}

export async function getCongestionSummary() {
  return request("/api/congestion/summary");
}

export function getStoredUser() {
  const user = localStorage.getItem("metroflow_user");

  if (!user) {
    return null;
  }

  try {
    return JSON.parse(user);
  } catch {
    return null;
  }
}