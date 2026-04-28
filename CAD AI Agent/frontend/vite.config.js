import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            "/upload": "http://localhost:4000",
            "/analyze": "http://localhost:4000",
            "/report": "http://localhost:4000",
            "/health": "http://localhost:4000",
            "/static": "http://localhost:4000"
        }
    }
});
