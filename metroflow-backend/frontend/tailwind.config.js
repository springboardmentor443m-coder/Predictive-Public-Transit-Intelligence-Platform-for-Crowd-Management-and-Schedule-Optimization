/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        metro: {
          dark: "#090d16",
          card: "#0f172a",
          cardBorder: "#1e293b",
          cyan: "#06b6d4",
          blue: "#3b82f6",
          magenta: "#ec4899",
          red: "#ef4444",
          yellow: "#eab308",
          emerald: "#10b981",
          purple: "#8b5cf6",
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Space Grotesk', 'Plus Jakarta Sans', 'sans-serif']
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)' },
          '100%': { boxShadow: '0 0 25px rgba(6, 182, 212, 0.8)' },
        }
      }
    },
  },
  plugins: [],
}
