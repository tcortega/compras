import { expect, test } from '@playwright/test'

const banned = /fraude|corrupto|roubo|flag|ranking/i

test('busca, lista e ficha de item com cobertura', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('strong').filter({ hasText: 'Cobertura incompleta' })).toBeVisible()
  await expect(page.getByText(/trimestre|trim\./i).first()).toBeVisible()
  await page.locator('#q-home').fill('dipirona')
  await page.getByRole('button', { name: 'Buscar' }).click()
  await expect(page.getByRole('heading', { name: /Resultados para/ })).toBeVisible()
  await page.getByRole('link', { name: /Dipirona sódica/ }).click()
  await expect(page.getByRole('heading', { name: /Dipirona sódica/ })).toBeVisible()
  await expect(page.getByText(/n=\d+/).first()).toBeVisible()
  await expect(page.getByText(/UF RJ/).first()).toBeVisible()
  await expect(page.getByText(/trimestre|trim\./i).first()).toBeVisible()
  await expect(page.getByText(/metodologia/i).first()).toBeVisible()
  await expect(page.locator('body')).not.toHaveText(banned)
})

test('órgão para contratação com denominador visível', async ({ page }) => {
  await page.goto('/orgaos')
  await page.getByRole('link', { name: /Prefeitura Municipal de Volta Redonda/ }).click()
  await expect(page.getByRole('heading', { name: /Prefeitura Municipal/ })).toBeVisible()
  await expect(page.getByText(/n=\d+/).first()).toBeVisible()
  await expect(page.getByText(/trimestre|trim\./i).first()).toBeVisible()
  await page.getByRole('link', { name: /gêneros alimentícios para a merenda/ }).click()
  await expect(page.getByText(/PNCP/).first()).toBeVisible()
  await expect(page.getByRole('strong').filter({ hasText: 'Cobertura incompleta' })).toBeVisible()
  await expect(page.getByText(/trimestre|trim\./i).first()).toBeVisible()
  await expect(page.locator('body')).not.toHaveText(banned)
})
