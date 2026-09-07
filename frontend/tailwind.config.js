/** @type {import('tailwindcss').Config} */
module.exports = {
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
        card: "0 1px 3px rgba(15,23,42,.08), 0 1px 2px rgba(15,23,42,.04)",
        pop: "0 10px 30px rgba(15,23,42,.12)",
      },
    },
  },
  plugins: [],
};
