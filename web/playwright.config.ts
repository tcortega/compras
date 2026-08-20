import { defineConfig, devices } from '@playwright/test'

const remote = process.env.PLAYWRIGHT_BASE_URL

export default defineConfig({
  testDir: './e2e',
  globalTeardown: './e2e/teardown.ts',
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
    : [
        {
          command:
            'TRIAGE_LABELS_PATH=/tmp/compras-triage-labels.csv TRIAGE_FLAGS_PATH=/tmp/compras-triage-flags.json COMPRAS_DATA_DIR=/tmp/compras-rotulos-e2e npm run dev',
          url: 'http://127.0.0.1:3000',
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
        {
          command:
            'STAGING_TRIAGE=0 NEXT_DIST_DIR=.next-rotulos-off npx next dev --port 3002',
          url: 'http://127.0.0.1:3002',
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
      ],
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testIgnore: /rotulos-off\.spec\.ts/,
    },
    ...(remote
      ? []
      : [
          {
            name: 'rotulos-off',
            use: { ...devices['Desktop Chrome'], baseURL: 'http://127.0.0.1:3002' },
            testMatch: /rotulos-off\.spec\.ts/,
          },
        ]),
  ],
})
