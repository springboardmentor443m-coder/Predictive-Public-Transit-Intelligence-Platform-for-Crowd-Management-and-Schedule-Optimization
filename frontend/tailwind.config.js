/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        metro: {
          bg: '#F7F5EF',
          card: '#FFFFFF',
          sidebar: '#E8E4D8',
          primary: '#2F6F68',
          secondary: '#6F8F87',
          healthy: '#4F8A63',
          warning: '#C58A3A',
          critical: '#B9574B',
          text: '#29322F',
          border: '#DDD9CF'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
