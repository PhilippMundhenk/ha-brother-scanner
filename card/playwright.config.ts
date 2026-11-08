import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './test',
  timeout: 30_000,
  retries: 0,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:4873',
    browserName: 'chromium',
  },
  webServer: {
    command: 'node test/serve.mjs 4873',
    url: 'http://localhost:4873/test/harness.html',
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
