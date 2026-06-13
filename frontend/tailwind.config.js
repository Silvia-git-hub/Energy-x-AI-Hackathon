/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        term: {
          bg:        "#080808",
          panel:     "#0e0e0e",
          border:    "#1c1c1c",
          amber:     "#f57c00",
          "amber-d": "#6b3900",
          dim:       "#444444",
          muted:     "#777777",
          text:      "#c8c8c8",
          bright:    "#eeeeee",
          green:     "#00c853",
          "green-d": "#00331a",
          red:       "#ff1744",
          "red-d":   "#440010",
          yellow:    "#ffd600",
          blue:      "#2979ff",
        },
      },
      keyframes: {
        ticker: {
          "0%":   { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "sun-spin": {
          "0%":   { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        "sun-pulse": {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0.55" },
        },
      },
      animation: {
        ticker:      "ticker 50s linear infinite",
        "sun-spin":  "sun-spin 14s linear infinite",
        "sun-pulse": "sun-pulse 3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
