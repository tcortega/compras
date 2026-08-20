import { expect, test, type Page } from '@playwright/test'

const banned = /fraude|corrupto|roubo|\bflag\b|ranking/i
const stubLeak = /7c2e1f40-3306-4050|Dipirona|Distribuidora de Medicamentos Serra|sha256:dev-slice-vr-2024/
const againstCompose = Boolean(process.env.PLAYWRIGHT_BASE_URL)
const niteroiName = /Prefeitura Municipal de Niter[oó]i/i
const bauruName = /Prefeitura Municipal de Bauru/i
const voltaName = /Prefeitura Municipal de Volta Redonda/i
const caxiasName = /Caxias do Sul/i
const joinvilleName = /Joinville/i

async function assertCoverageAndBan(page: Page) {
  await expect(page.getByText(/n=\d+/).first()).toBeVisible()
  await expect(page.getByText(/UF RJ|UF SP|UF RS|UF SC|UF mista|filtro sem registros/).first()).toBeVisible()
  await expect(page.getByText(/trimestre|trim\./i).first()).toBeVisible()
  await expect(page.getByText(/metodologia/i).first()).toBeVisible()
  await expect(page.locator('body')).not.toHaveText(banned)
  if (againstCompose) {
    await expect(page.locator('body')).not.toHaveText(stubLeak)
  }
}

test('home cards usam o n da coleção, não o n de itens', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('strong').filter({ hasText: 'Cobertura incompleta' })).toBeVisible()
  await expect(page.getByText(/UF mista/).first()).toBeVisible()
  await expect(page.getByText(/Caxias do Sul \(RS\) e Joinville \(SC\)/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  const orgaos = page.locator('.index-card', { has: page.getByText('Órgãos', { exact: true }) })
  const itens = page.locator('.index-card', { has: page.getByText('Itens', { exact: true }) })
  const orgaosN = (await orgaos.getByRole('strong').innerText()).replace(/\D/g, '')
  const itensN = (await itens.getByRole('strong').innerText()).replace(/\D/g, '')
  await expect(orgaos.getByText(new RegExp(`n=${orgaosN}`))).toBeVisible()
  await expect(itens.getByText(new RegExp(`n=${itensN}`))).toBeVisible()
  expect(orgaosN).not.toEqual(itensN)
  if (!againstCompose) {
    await expect(orgaos.getByRole('strong')).toHaveText('8')
    await expect(itens.getByRole('strong')).toHaveText('32')
  }

  if (againstCompose) {
    await page.goto('/itens')
    const itemLink = page.locator('table.data tbody a').first()
    await expect(itemLink).toBeVisible()
    const itemName = (await itemLink.innerText()).trim()
    const token = itemName.split(/\s+/).find((word) => word.length >= 4) ?? itemName
    await page.goto('/')
    await page.locator('#q-home').fill(token)
    await page.getByRole('button', { name: 'Buscar' }).click()
    await expect(page.getByRole('heading', { name: /Resultados para/ })).toBeVisible()
    await page.getByRole('link', { name: itemName }).first().click()
    await expect(page.getByRole('heading', { name: itemName })).toBeVisible()
    await expect(page.getByText(/R\$\s*[\d.]+,\d{2}/).first()).toBeVisible()
  } else {
    await page.locator('#q-home').fill('dipirona')
    await page.getByRole('button', { name: 'Buscar' }).click()
    await expect(page.getByRole('heading', { name: /Resultados para/ })).toBeVisible()
    await page.getByRole('link', { name: /Dipirona sódica/ }).click()
    await expect(page.getByRole('heading', { name: /Dipirona sódica/ })).toBeVisible()
    await expect(page.getByText('R$ 0,18').first()).toBeVisible()
  }
  await assertCoverageAndBan(page)
})

test('órgão para contratação com denominador visível', async ({ page }) => {
  await page.goto('/orgaos')
  await page.getByRole('link', { name: voltaName }).click()
  await expect(page.getByText(/volta redonda/i).first()).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Contratações' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Itens' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await assertCoverageAndBan(page)

  await page
    .locator('section', { has: page.getByRole('heading', { name: 'Contratações' }) })
    .locator('table.data tbody a')
    .first()
    .click()
  await expect(page.getByText(/PNCP/).first()).toBeVisible()
  await expect(page.getByRole('strong').filter({ hasText: 'Cobertura incompleta' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Fonte' })).toHaveCount(0)
  await expect(page.getByText(/R\$\s*[\d.]+,\d{2}/).first()).toBeVisible()
  await expect(page.getByText(/\d{2}\/\d{2}\/\d{4}/).first()).toBeVisible()
  await assertCoverageAndBan(page)
})

test('filtra município IBGE e UF e mantém cobertura no vazio', async ({ page }) => {
  await page.goto('/orgaos')
  await expect(page.getByRole('link', { name: niteroiName })).toBeVisible()
  await expect(page.getByRole('link', { name: bauruName })).toBeVisible()
  await expect(page.getByRole('link', { name: caxiasName })).toBeVisible()
  await expect(page.getByRole('link', { name: joinvilleName })).toBeVisible()
  await expect(page.getByText(/UF mista/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.locator('input[name="municipioIbge"]').fill('3303302')
  await page.getByRole('button', { name: 'Filtrar' }).click()
  const niteroiTable = page.locator('table.data')
  await expect(niteroiTable.getByRole('link', { name: niteroiName })).toBeVisible()
  await expect(niteroiTable.getByRole('link', { name: bauruName })).toHaveCount(0)
  await expect(niteroiTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF RJ/).first()).toBeVisible()
  await niteroiTable.getByRole('link', { name: niteroiName }).click()
  await expect(page.getByRole('heading', { name: /Niter[oó]i/i })).toBeVisible()
  await expect(page.getByText('3303302', { exact: true })).toBeVisible()
  await assertCoverageAndBan(page)
  await page.goto('/orgaos?municipioIbge=3303302')

  await page.goto('/orgaos?uf=SP')
  const bauruTable = page.locator('table.data')
  await expect(bauruTable.getByRole('link', { name: bauruName })).toBeVisible()
  await expect(bauruTable.getByRole('link', { name: niteroiName })).toHaveCount(0)
  await expect(bauruTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF SP/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/itens?uf=SP')
  await expect(page.getByText(/UF SP/).first()).toBeVisible()
  await expect(page.locator('table.data tbody tr').first()).toBeVisible()
  if (!againstCompose) {
    await expect(page.getByRole('link', { name: /Papel A4 75 g/ })).toBeVisible()
    await expect(page.getByText(/n=2/).first()).toBeVisible()
  }
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?municipioIbge=4305108')
  const caxiasTable = page.locator('table.data')
  await expect(caxiasTable.getByRole('link', { name: caxiasName })).toBeVisible()
  await expect(caxiasTable.getByRole('link', { name: joinvilleName })).toHaveCount(0)
  await expect(caxiasTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF RS/).first()).toBeVisible()
  await caxiasTable.getByRole('link', { name: caxiasName }).click()
  await expect(page.getByRole('heading', { name: /Caxias do Sul/i })).toBeVisible()
  await expect(page.getByText('4305108', { exact: true })).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?uf=SC')
  const joinvilleTable = page.locator('table.data')
  await expect(joinvilleTable.getByRole('link', { name: joinvilleName })).toBeVisible()
  await expect(joinvilleTable.getByRole('link', { name: caxiasName })).toHaveCount(0)
  await expect(joinvilleTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF SC/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/itens?uf=SC')
  await expect(page.getByText(/UF SC/).first()).toBeVisible()
  await expect(page.locator('table.data tbody tr').first()).toBeVisible()
  if (!againstCompose) {
    await expect(page.getByRole('link', { name: /Leitora c[oó]digo/ })).toBeVisible()
    await expect(page.getByText(/n=1/).first()).toBeVisible()
  }
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?q=zzzz-sem-registro')
  await expect(page.getByText('Nenhum registro neste recorte para o filtro atual.')).toBeVisible()
  await expect(page.getByText(/n=0/).first()).toBeVisible()
  await expect(page.getByText(/filtro sem registros/).first()).toBeVisible()
  await expect(page.getByText(/metodologia/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?uf=RJ&q=zzzz-sem-registro')
  await expect(page.getByText(/n=0/).first()).toBeVisible()
  await expect(page.getByText(/UF RJ/).first()).toBeVisible()
  await expect(page.getByText(/metodologia/).first()).toBeVisible()
  await assertCoverageAndBan(page)
})

test('ficha de fornecedor não apresenta Homologado como total', async ({ page }) => {
  await page.goto('/fornecedores')
  await page.locator('table.data tbody a').first().click()
  await expect(page.locator('.stats .kicker', { hasText: 'Contratações' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Itens' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await assertCoverageAndBan(page)
})

test('vazio, 404 e páginas estáticas mantêm cobertura e o banimento', async ({ page }) => {
  await page.goto('/orgaos?q=zzzz-sem-registro')
  await expect(page.getByText('Nenhum registro neste recorte para o filtro atual.')).toBeVisible()
  await expect(page.getByText(/n=0/).first()).toBeVisible()
  await expect(page.getByText(/filtro sem registros/).first()).toBeVisible()
  await expect(page.getByText(/metodologia/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/orgaos/00000000-0000-0000-0000-000000000000')
  await expect(page.getByRole('heading', { name: /não encontrado/ })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Voltar ao início' })).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/cobertura')
  await expect(page.getByRole('heading', { name: 'Cobertura incompleta' })).toBeVisible()
  await expect(page.getByText(/3303302/).first()).toBeVisible()
  await expect(page.getByText(/3506003/).first()).toBeVisible()
  await expect(page.getByText(/4305108/).first()).toBeVisible()
  await expect(page.getByText(/4209102/).first()).toBeVisible()
  await expect(page.getByText(/não é um total nacional/).first()).toBeVisible()
  await expect(page.getByText(/UF mista/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/metodologia')
  await expect(page.getByRole('heading', { name: /Metodologia/ })).toBeVisible()
  await assertCoverageAndBan(page)
})
