/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./pages/**/*.{js,jsx}", "./components/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef6ff",
          100: "#d9ebff",
          200: "#bcdcff",
          300: "#8ec6ff",
          400: "#59a5ff",
          500: "#3382fc",
          600: "#1d62f1",
          700: "#154bde",
          800: "#183eb4",
          900: "#1a388e",
          950: "#152556",
        },
        slate: {
          950: "#090d16",
          900: "#0f172a",
          850: "#131d33",
          800: "#1e293b",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.04)",
        pop: "0 10px 30px rgba(0,0,0,.25)",
        glow: "0 0 20px rgba(29, 98, 241, 0.35)",
        "glow-emerald": "0 0 20px rgba(16, 185, 129, 0.35)",
        "glow-rose": "0 0 20px rgba(244, 63, 94, 0.35)",
        "glow-amber": "0 0 20px rgba(245, 158, 11, 0.35)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "radar-spin": "radar 4s linear infinite",
        "float": "float 3s ease-in-out infinite",
      },
      keyframes: {
        radar: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        }
      }
    },
  },
  plugins: [],
};

