import { defineConfig, devices } from '@playwright/test'

const remote = process.env.PLAYWRIGHT_BASE_URL

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: remote || 'http://127.0.0.1:3000',
    locale: 'pt-BR',
    trace: 'on-first-retry',
  },
  webServer: remote
    ? undefined
    : {
        command: 'TRIAGE_LABELS_PATH=/tmp/compras-triage-labels.csv npm run dev',
        url: 'http://127.0.0.1:3000',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
