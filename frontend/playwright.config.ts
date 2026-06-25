import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:3005',
    headless: true,
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      command: 'AUTH_DISABLED=true ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --app-dir .',
      cwd: '../backend',
      url: 'http://127.0.0.1:4000/api/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: 'NEXT_PUBLIC_AUTH_DISABLED=true npm run dev',
      cwd: '.',
      url: 'http://127.0.0.1:3005',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
});
