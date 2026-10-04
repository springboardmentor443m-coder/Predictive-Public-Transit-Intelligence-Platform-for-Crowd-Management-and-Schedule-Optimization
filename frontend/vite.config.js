import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    watch: {
      // Bind mounts on Docker Desktop do not propagate inotify events from the
      // host into the Linux VM, so the default watcher silently misses edits.
      // Polling picks them up reliably (at a small CPU cost).
      usePolling: true,
      interval: 1000,
    },
  },
})