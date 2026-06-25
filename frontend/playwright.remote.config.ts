import { defineConfig, devices } from '@playwright/test';

const remoteBaseUrl = process.env.AXISARCH_REMOTE_URL || 'http://localhost:8080';

export default defineConfig({
  testDir: './e2e',
  timeout: 10 * 60 * 1000,
  expect: {
    timeout: 20_000,
  },
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: remoteBaseUrl,
    headless: false,
    ignoreHTTPSErrors: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        browserName: 'chromium',
      },
    },
  ],
});