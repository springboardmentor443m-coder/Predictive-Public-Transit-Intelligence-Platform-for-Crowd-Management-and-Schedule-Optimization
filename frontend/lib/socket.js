import { io } from "socket.io-client";

// Empty/unset NEXT_PUBLIC_API_URL -> same-origin socket (proxied by
// next.config.js rewrites to BACKEND_INTERNAL_URL in container deployments).
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

let socket = null;

export function getSocket() {
  if (socket && socket.connected) return socket;
  socket = io(API_URL, {
    path: "/socket.io",
    transports: ["websocket", "polling"],
    reconnectionAttempts: 5,
    timeout: 5000,
  });
  return socket;
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}
