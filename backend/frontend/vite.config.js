import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    assetsDir: "frontend-assets"
  },
  server: {
    proxy: {
      "/upload": "http://127.0.0.1:8000",
      "/ask": "http://127.0.0.1:8000",
      "/pdf": "http://127.0.0.1:8000",
      "/page": "http://127.0.0.1:8000",
      "/assets": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000"
    }
  }
});
