/**
 * The neutral palette is driven by CSS custom properties declared in
 * styles/globals.css so a single token swap re-themes the entire product.
 * Dark values live on :root, light values on html.light.
 */
const slate = (shade) => `rgb(var(--mf-slate-${shade}) / <alpha-value>)`;

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./pages/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}", "./lib/**/*.{js,ts,tsx}"],
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
          50: slate(50),
          100: slate(100),
          200: slate(200),
          300: slate(300),
          400: slate(400),
          500: slate(500),
          600: slate(600),
          700: slate(700),
          800: slate(800),
          850: slate(850),
          900: slate(900),
          950: slate(950),
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
        glow: "var(--mf-glow-brand)",
        "glow-emerald": "var(--mf-glow-emerald)",
        "glow-rose": "var(--mf-glow-rose)",
        "glow-amber": "var(--mf-glow-amber)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "radar-spin": "radar 4s linear infinite",
        "float": "float 3s ease-in-out infinite",
        "toast-in": "toast-in 300ms cubic-bezier(0.16, 1, 0.3, 1)",
      },
      keyframes: {
        radar: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        },
        "toast-in": {
          "0%": { opacity: "0", transform: "translateX(24px) scale(0.97)" },
          "100%": { opacity: "1", transform: "translateX(0) scale(1)" },
        },
      },
    },
  },
  plugins: [],
};
