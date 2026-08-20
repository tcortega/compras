import { expect, test, type Page } from '@playwright/test'

const banned = /fraude|corrupto|roubo|flag|ranking/i

async function assertCoverageAndBan(page: Page) {
  await expect(page.getByText(/n=\d+/).first()).toBeVisible()
  await expect(page.getByText(/UF RJ|filtro sem registros/).first()).toBeVisible()
  await expect(page.getByText(/trimestre|trim\./i).first()).toBeVisible()
  await expect(page.getByText(/metodologia/i).first()).toBeVisible()
  await expect(page.locator('body')).not.toHaveText(banned)
}

test('home cards usam o n da coleção, não o n de itens', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('strong').filter({ hasText: 'Cobertura incompleta' })).toBeVisible()
  await assertCoverageAndBan(page)

  const orgaos = page.locator('.index-card', { has: page.getByText('Órgãos', { exact: true }) })
  await expect(orgaos.getByRole('strong')).toHaveText('4')
  await expect(orgaos.getByText(/n=4/)).toBeVisible()

  const itens = page.locator('.index-card', { has: page.getByText('Itens', { exact: true }) })
  await expect(itens.getByRole('strong')).toHaveText('26')
  await expect(itens.getByText(/n=26/)).toBeVisible()

  await page.locator('#q-home').fill('dipirona')
  await page.getByRole('button', { name: 'Buscar' }).click()
  await expect(page.getByRole('heading', { name: /Resultados para/ })).toBeVisible()
  await page.getByRole('link', { name: /Dipirona sódica/ }).click()
  await expect(page.getByRole('heading', { name: /Dipirona sódica/ })).toBeVisible()
  await expect(page.getByText('R$ 0,18').first()).toBeVisible()
  await assertCoverageAndBan(page)
})

test('órgão para contratação com denominador visível', async ({ page }) => {
  await page.goto('/orgaos')
  await page.getByRole('link', { name: /Prefeitura Municipal de Volta Redonda/ }).click()
  await expect(page.getByRole('heading', { name: /Prefeitura Municipal/ })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Contratações' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Itens' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await assertCoverageAndBan(page)
  await page.getByRole('link', { name: /gêneros alimentícios para a merenda/ }).click()
  await expect(page.getByText(/PNCP/).first()).toBeVisible()
  await expect(page.getByRole('strong').filter({ hasText: 'Cobertura incompleta' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Fonte' })).toHaveCount(0)
  await assertCoverageAndBan(page)
})

test('ficha de fornecedor não apresenta Homologado como total', async ({ page }) => {
  await page.goto('/fornecedores')
  await page.getByRole('link', { name: /Distribuidora de Medicamentos Serra/ }).click()
  await expect(page.getByRole('heading', { name: /Distribuidora de Medicamentos Serra/ })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Contratações' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Itens' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await assertCoverageAndBan(page)
})

test('vazio, 404 e páginas estáticas mantêm cobertura e o banimento', async ({ page }) => {
  await page.goto('/orgaos?q=zzzz-sem-registro')
  await expect(page.getByText('Nenhum registro neste recorte para o filtro atual.')).toBeVisible()
  await expect(page.getByText(/n=0/).first()).toBeVisible()
  await expect(page.getByText(/UF RJ/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/orgaos/00000000-0000-0000-0000-000000000000')
  await expect(page.getByRole('heading', { name: /não encontrado/ })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Voltar ao início' })).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/cobertura')
  await expect(page.getByRole('heading', { name: 'Cobertura incompleta' })).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/metodologia')
  await expect(page.getByRole('heading', { name: /Metodologia/ })).toBeVisible()
  await assertCoverageAndBan(page)
})
