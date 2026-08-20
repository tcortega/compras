import { expect, test } from '@playwright/test'
import { againstCompose, assertCoverageAndBan, firstTableName } from './busca-helpers'

test('busca um item plantado e abre a ficha ou lista o item', async ({ page }) => {
  const name = againstCompose ? await firstTableName(page, '/itens') : 'Dipirona sódica 500 mg'
  const token = name.split(/\s+/).find((word) => word.length >= 4) ?? name
  await page.goto(`/busca?q=${encodeURIComponent(token)}`)
  await expect(page.getByRole('heading', { name: /Resultados para/ })).toBeVisible()
  if (againstCompose) {
    await expect(page.getByText(/Índice Meilisearch/)).toBeVisible()
  } else {
    await expect(page.getByText(/Filtro do recorte \(warehouse\)/)).toBeVisible()
  }
  const itemLink = page.locator('section', { has: page.getByRole('heading', { name: 'Itens' }) }).getByRole('link', { name })
  await expect(itemLink.first()).toBeVisible()
  await itemLink.first().click()
  await expect(page).toHaveURL(/\/itens\//)
  await expect(page.getByRole('heading', { name })).toBeVisible()
  await assertCoverageAndBan(page)
})
