import { expect, test } from '@playwright/test'
import { againstCompose, assertCoverageAndBan, firstTableName } from './busca-helpers'

test('busca um órgão plantado e lista esse órgão', async ({ page }) => {
  const name = againstCompose ? await firstTableName(page, '/orgaos?take=100') : 'Prefeitura Municipal de Volta Redonda'
  const token = name.includes('Volta Redonda') ? 'Volta Redonda' : name
  await page.goto(`/busca?q=${encodeURIComponent(token)}`)
  await expect(page.getByRole('heading', { name: /Resultados para/ })).toBeVisible()
  const orgaoLink = page.locator('section', { has: page.getByRole('heading', { name: 'Órgãos' }) }).getByRole('link', { name: new RegExp(token, 'i') })
  await expect(orgaoLink.first()).toBeVisible()
  await assertCoverageAndBan(page)
})
