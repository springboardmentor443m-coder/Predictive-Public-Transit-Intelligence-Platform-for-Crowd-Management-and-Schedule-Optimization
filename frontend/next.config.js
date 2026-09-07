/** @type {import('next').NextConfig} */
const BACKEND_INTERNAL_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "",
    BACKEND_INTERNAL_URL,
  },
  async rewrites() {
    // Server-side proxy so the browser can use same-origin URLs
    // (NEXT_PUBLIC_API_URL="") in Docker/Kubernetes deployments where
    // cluster-internal hostnames are not reachable from the client.
    return [
      { source: "/api/v1/:path*", destination: `${BACKEND_INTERNAL_URL}/api/v1/:path*` },
      { source: "/socket.io/:path*", destination: `${BACKEND_INTERNAL_URL}/socket.io/:path*` },
    ];
  },
};

module.exports = nextConfig;
