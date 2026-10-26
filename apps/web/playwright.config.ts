import { defineConfig, devices } from "@playwright/test";

const port = process.env.PLAYWRIGHT_PORT ?? "3002";
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  reporter: "list",
  projects: [
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } },
    },
    {
      name: "mobile",
      use: { ...devices["Desktop Chrome"], viewport: { width: 390, height: 844 }, isMobile: true },
    },
  ],
  use: {
    baseURL,
    trace: "retain-on-failure",
  },
  webServer: process.env.PLAYWRIGHT_EXTERNAL_SERVERS
    ? undefined
    : {
        command: `corepack pnpm dev --hostname 127.0.0.1 --port ${port}`,
        url: baseURL,
        reuseExistingServer: false,
        env: { NEXT_PUBLIC_API_URL: baseURL },
        timeout: 120_000,
      },
});
