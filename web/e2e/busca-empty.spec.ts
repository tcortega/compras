import { expect, test } from '@playwright/test'
import { assertCoverageAndBan } from './busca-helpers'

test('q vazio mantém coverage.n do recorte', async ({ page }) => {
  await page.goto('/itens')
  const itensN = (await page.getByText(/n=\d+/).first().innerText()).replace(/\D/g, '')
  await page.goto('/busca')
  await expect(page.getByRole('heading', { name: 'Buscar no recorte' })).toBeVisible()
  await expect(page.getByText(/n=\d+/).first()).toBeVisible()
  const buscaN = (await page.getByText(/n=\d+/).first().innerText()).replace(/\D/g, '')
  expect(buscaN).toBe(itensN)
  await expect(page.getByRole('heading', { name: 'Órgãos' })).toHaveCount(0)
  await assertCoverageAndBan(page)
})
