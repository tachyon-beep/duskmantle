import { defineConfig } from '@playwright/test';

const port = parseInt(process.env.PLAYWRIGHT_PORT ?? '8765', 10);
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: './playwright/tests',
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL,
    trace: process.env.CI ? 'on-first-retry' : 'retain-on-failure',
    video: 'off',
  },
  webServer: {
    command: 'python tests/playwright_server.py',
    url: `${baseURL}/readyz`,
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
  },
});
