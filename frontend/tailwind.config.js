/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        display: ["Outfit", "system-ui", "sans-serif"],
      },
      colors: {
        ink: { 950: "#0c0f14", 900: "#121722", 800: "#1a2230" },
        accent: { DEFAULT: "#3b82f6", glow: "#60a5fa" },
        surface: "#151b27",
      },
    },
  },
  plugins: [],
};
