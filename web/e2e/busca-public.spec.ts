import { expect, test } from '@playwright/test'
import { assertCoverageAndBan } from './busca-helpers'

test('busca pública sem campos de sinal, homologado ou triagem no nav', async ({ page }) => {
  await page.goto('/busca?q=papel')
  await assertCoverageAndBan(page)
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Seções"] a[href="/interno/triagem"]')).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Rodapé"] a[href="/interno/triagem"]')).toHaveCount(0)
  await expect(page.locator('body')).not.toHaveText(/fraude|corrupto|ranking|adjacenc|shared_qsa/i)

  await page.goto('/orgaos')
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await page.goto('/fornecedores')
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Seções"] a[href="/interno/triagem"]')).toHaveCount(0)
})
