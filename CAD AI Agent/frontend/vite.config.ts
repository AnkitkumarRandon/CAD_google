import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/upload": "https://your-backend-url.onrender.com",
      "/analyze": "https://your-backend-url.onrender.com",
      "/report": "https://your-backend-url.onrender.com",
      "/health": "https://your-backend-url.onrender.com",
      "/static": "https://your-backend-url.onrender.com"
    }
  }
});
