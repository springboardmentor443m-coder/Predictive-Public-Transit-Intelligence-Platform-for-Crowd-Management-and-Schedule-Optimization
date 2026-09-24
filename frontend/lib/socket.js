import { io } from "socket.io-client";

// Empty/unset NEXT_PUBLIC_API_URL -> same-origin socket (proxied by
// next.config.js rewrites to BACKEND_INTERNAL_URL in container deployments).
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

let socket = null;
let joinedStation = null;
let joinedTrain = null;

function authPayload() {
  if (typeof window === "undefined") return undefined;
  try {
    const token = sessionStorage.getItem("metroflow_token");
    return token ? { token } : undefined;
  } catch {
    return undefined;
  }
}

export function getSocket() {
  if (socket && socket.connected) return socket;
  if (socket) {
    try { socket.disconnect(); } catch {}
    socket = null;
  }
  socket = io(API_URL, {
    path: "/socket.io",
    transports: ["websocket", "polling"],
    reconnectionAttempts: 10,
    reconnectionDelay: 2000,
    timeout: 8000,
    auth: authPayload(),
  });
  // Re-join station/train rooms after reconnects.
  socket.on("connect", () => {
    if (joinedStation) socket.emit("join_station", { station_id: joinedStation });
    if (joinedTrain) socket.emit("join_train", { train_id: joinedTrain });
  });
  return socket;
}

export function joinStationRoom(stationId) {
  joinedStation = stationId || null;
  try {
    const s = getSocket();
    if (stationId) s.emit("join_station", { station_id: stationId });
  } catch {}
}

export function leaveStationRoom() {
  try {
    if (socket && joinedStation) socket.emit("leave_station", { station_id: joinedStation });
  } catch {}
  joinedStation = null;
}

export function joinTrainRoom(trainId) {
  joinedTrain = trainId || null;
  try {
    const s = getSocket();
    if (trainId) s.emit("join_train", { train_id: trainId });
  } catch {}
}

export function leaveTrainRoom() {
  try {
    if (socket && joinedTrain) socket.emit("leave_train", { train_id: joinedTrain });
  } catch {}
  joinedTrain = null;
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}
