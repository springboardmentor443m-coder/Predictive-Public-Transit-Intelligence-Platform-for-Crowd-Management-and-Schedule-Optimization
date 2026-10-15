/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'navy-base': '#0B1220',
        'navy-panel': '#111827',
        'navy-subtle': '#162032',
        'teal-accent': '#00D4AA',
      },
    },
  },
  plugins: [],
}
