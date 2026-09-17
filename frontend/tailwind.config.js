/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Neo-Seoul Deep Void Obsidian & Quantum Slate
        bg: {
          main: "#080912",
          surface: "#0F1222",
          card: "#161B30",
          subtle: "#1F2642",
          hover: "#222B4A",
        },
        border: {
          dark: "#283256",
          subtle: "#1D243E",
          glow: "rgba(168, 85, 247, 0.4)",
          tealGlow: "rgba(0, 245, 212, 0.35)",
        },
        // Holographic Electric Violet & Cyber Aurora Accents
        metro: {
          primary: "#A855F7",       // Electric Orchid Violet
          primaryHover: "#C084FC",  // Luminous Violet
          cyan: "#00F5D4",          // Aurora Neon Teal
          cyanHover: "#05FFA1",     // Bioluminescent Mint
          amber: "#FFBE0B",         // Cyber Solar Gold
          indigo: "#6366F1",        // Quantum Indigo
          rose: "#FF007F",          // Neon Laser Rose
        },
        // 4 Ultra-Vivid, Non-Generic Congestion States
        congestion: {
          low: "#05FFA1",       // Bioluminescent Aurora Mint (Normal flow, <40%)
          medium: "#00E5FF",    // Electric Laser Topaz Cyan (Moderate flow, 40-67%)
          high: "#FF9E00",      // Hyper Solar Tangerine (Elevated flow, 68-85%)
          critical: "#FF0055",  // Ultraviolet Hyper-Crimson (Overcrowded, >=86%)
        }
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "Outfit", "Inter", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(168, 85, 247, 0.35)",
        tealGlow: "0 0 20px rgba(0, 245, 212, 0.35)",
        card: "0 6px 24px -2px rgba(0, 0, 0, 0.65)",
        critGlow: "0 0 22px rgba(255, 0, 85, 0.55)",
        lowGlow: "0 0 18px rgba(5, 255, 161, 0.45)",
      }
    },
  },
  plugins: [],
}
