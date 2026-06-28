import { defineConfig } from "@playwright/test";

const BACKEND = "http://127.0.0.1:11072";
const FRONTEND = "http://127.0.0.1:11073";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: FRONTEND,
    headless: true,
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `uv run python -m glama_status_mcp --http --port 11072`,
      port: 11072,
      cwd: "../",
      timeout: 30000,
      reuseExistingServer: true,
    },
  ],
});
