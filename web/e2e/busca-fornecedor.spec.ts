import { expect, test } from '@playwright/test'
import { againstCompose, assertCoverageAndBan, firstTableName } from './busca-helpers'

test('busca um fornecedor plantado e lista esse fornecedor', async ({ page }) => {
  const name = againstCompose
    ? await firstTableName(page, '/fornecedores')
    : 'Distribuidora de Medicamentos Serra Ltda'
  const token = name.split(/\s+/).find((word) => word.length >= 5) ?? name
  await page.goto(`/busca?q=${encodeURIComponent(token)}`)
  await expect(page.getByRole('heading', { name: /Resultados para/ })).toBeVisible()
  const link = page
    .locator('section', { has: page.getByRole('heading', { name: 'Fornecedores' }) })
    .getByRole('link', { name: new RegExp(token, 'i') })
  await expect(link.first()).toBeVisible()
  await assertCoverageAndBan(page)
})
