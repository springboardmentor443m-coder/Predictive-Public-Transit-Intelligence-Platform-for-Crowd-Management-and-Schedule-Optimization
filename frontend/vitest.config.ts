import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["**/*.{test,spec}.{ts,tsx}"],
    // node_modules and the Next build output are never sources of tests
    exclude: ["node_modules/**", ".next/**", "out/**"],
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, "./") },
  },
});
