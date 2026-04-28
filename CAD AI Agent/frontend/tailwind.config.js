/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        glow: "#8cf4d3"
      },
      boxShadow: {
        neon: "0 24px 80px rgba(12, 255, 198, 0.18)"
      },
      fontFamily: {
        display: ['"Space Grotesk"', "sans-serif"],
        body: ['"Manrope"', "sans-serif"]
      }
    }
  },
  plugins: []
};
