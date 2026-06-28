import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 11073,
    proxy: {
      "/api": "http://127.0.0.1:11072",
      "/health": "http://127.0.0.1:11072",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
