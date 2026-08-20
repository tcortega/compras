import { expect, test } from '@playwright/test'

test('rotulos some com STAGING_TRIAGE=0', async ({ page }) => {
  const res = await page.goto('/interno/rotulos')
  expect(res?.status()).toBe(404)
  await expect(page.getByRole('heading', { name: 'Registro não encontrado neste recorte.' })).toBeVisible()
  await expect(page.locator('a[href="/interno/rotulos"]')).toHaveCount(0)
})
