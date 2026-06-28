import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    port: 11073,
    proxy: {
      "/api": "http://127.0.0.1:11072",
      "/health": "http://127.0.0.1:11072",
      "/mcp": "http://127.0.0.1:11072",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
