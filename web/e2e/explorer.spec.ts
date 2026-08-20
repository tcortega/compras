import { expect, test, type Page } from '@playwright/test'

const banned = /fraude|corrupto|roubo|\bflag\b|ranking/i
const stubLeak = /7c2e1f40-3306-4050|Dipirona|Distribuidora de Medicamentos Serra|sha256:dev-slice-vr-2024/
const againstCompose = Boolean(process.env.PLAYWRIGHT_BASE_URL)
const niteroiName = /Prefeitura Municipal de Niter[oó]i/i
const bauruName = /Prefeitura Municipal de Bauru/i
const voltaName = /Prefeitura Municipal de Volta Redonda/i
const caxiasName = /Munic[ií]pio de Caxias do Sul/i
const joinvilleName = /Munic[ií]pio de Joinville/i
const uberlandiaName = /Munic[ií]pio de Uberl[aâ]ndia/i
const londrinaName = /Munic[ií]pio de Londrina/i
const feiraName = /Munic[ií]pio de Feira de Santana/i
const caruaruName = /Munic[ií]pio de Caruaru/i
const anapolisName = /Munic[ií]pio de An[aá]polis/i
const vilaVelhaName = /Munic[ií]pio de Vila Velha/i
const campinaName = /Munic[ií]pio de Campina Grande/i
const caucaiaName = /Munic[ií]pio de Caucaia/i

async function assertCoverageAndBan(page: Page) {
  await expect(page.getByText(/n=\d+/).first()).toBeVisible()
  await expect(page.getByText(/UF RJ|UF SP|UF RS|UF SC|UF MG|UF PR|UF BA|UF PE|UF GO|UF ES|UF PB|UF CE|UF mista|filtro sem registros/).first()).toBeVisible()
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
  await expect(page.getByText(/Caxias do Sul \(RS\), Joinville \(SC\), Uberlândia \(MG\), Londrina \(PR\), Feira de Santana \(BA\), Caruaru \(PE\), Anápolis \(GO\), Vila Velha \(ES\), Campina Grande \(PB\) e Caucaia \(CE\)/).first()).toBeVisible()
  const brand = page.locator('.brand-kicker')
  await expect(brand).toHaveText(/treze municípios · 2024/i)
  await expect(brand).not.toHaveText(/Caxias do Sul|Uberlândia|Londrina|Feira de Santana|Caruaru|Anápolis|Vila Velha|Campina Grande|Caucaia/)
  const brandBox = await brand.boundingBox()
  const masthead = await page.locator('.masthead-inner').boundingBox()
  expect(brandBox).toBeTruthy()
  expect(masthead).toBeTruthy()
  expect(brandBox!.width).toBeLessThanOrEqual(masthead!.width)
  await page.setViewportSize({ width: 390, height: 844 })
  const narrowBrand = await brand.boundingBox()
  const narrowMasthead = await page.locator('.masthead-inner').boundingBox()
  expect(narrowBrand!.width).toBeLessThanOrEqual(narrowMasthead!.width)
  await page.setViewportSize({ width: 1280, height: 720 })
  await assertCoverageAndBan(page)

  const orgaos = page.locator('.index-card', { has: page.getByText('Órgãos', { exact: true }) })
  const itens = page.locator('.index-card', { has: page.getByText('Itens', { exact: true }) })
  const orgaosN = (await orgaos.getByRole('strong').innerText()).replace(/\D/g, '')
  const itensN = (await itens.getByRole('strong').innerText()).replace(/\D/g, '')
  await expect(orgaos.getByText(new RegExp(`n=${orgaosN}`))).toBeVisible()
  await expect(itens.getByText(new RegExp(`n=${itensN}`))).toBeVisible()
  expect(orgaosN).not.toEqual(itensN)
  if (!againstCompose) {
    await expect(orgaos.getByRole('strong')).toHaveText('16')
    await expect(itens.getByRole('strong')).toHaveText('40')
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
  await page.locator('table.data').getByRole('link', { name: voltaName }).click()
  await expect(page.getByText(/volta redonda/i).first()).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Contratações' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Itens' })).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await expect(
    page
      .locator('section', { has: page.getByRole('heading', { name: 'Contratações' }) })
      .getByText(/\d{2}\/\d{2}\/\d{4}/)
      .first(),
  ).toBeVisible()
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
  const publishedTable = page.locator('table.data')
  await expect(publishedTable.getByRole('link', { name: niteroiName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: bauruName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: caxiasName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: joinvilleName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: uberlandiaName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: londrinaName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: feiraName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: caruaruName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: anapolisName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: vilaVelhaName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: campinaName })).toBeVisible()
  await expect(publishedTable.getByRole('link', { name: caucaiaName })).toBeVisible()
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
  await expect(page.getByRole('heading', { name: caxiasName })).toBeVisible()
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

  await page.goto('/orgaos?municipioIbge=3170206')
  const uberlandiaTable = page.locator('table.data')
  await expect(uberlandiaTable.getByRole('link', { name: uberlandiaName })).toBeVisible()
  await expect(uberlandiaTable.getByRole('link', { name: londrinaName })).toHaveCount(0)
  await expect(uberlandiaTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF MG/).first()).toBeVisible()
  await uberlandiaTable.getByRole('link', { name: uberlandiaName }).click()
  await expect(page.getByRole('heading', { name: uberlandiaName })).toBeVisible()
  await expect(page.getByText('3170206', { exact: true })).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?uf=PR')
  const londrinaTable = page.locator('table.data')
  await expect(londrinaTable.getByRole('link', { name: londrinaName })).toBeVisible()
  await expect(londrinaTable.getByRole('link', { name: uberlandiaName })).toHaveCount(0)
  await expect(londrinaTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF PR/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/itens?uf=PR')
  await expect(page.getByText(/UF PR/).first()).toBeVisible()
  await expect(page.locator('table.data tbody tr').first()).toBeVisible()
  if (!againstCompose) {
    await expect(page.getByRole('link', { name: /Clindamicina/ })).toBeVisible()
    await expect(page.getByText(/n=1/).first()).toBeVisible()
  }
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?municipioIbge=2910800')
  const feiraTable = page.locator('table.data')
  await expect(feiraTable.getByRole('link', { name: feiraName })).toBeVisible()
  await expect(feiraTable.getByRole('link', { name: caruaruName })).toHaveCount(0)
  await expect(feiraTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF BA/).first()).toBeVisible()
  await feiraTable.getByRole('link', { name: feiraName }).click()
  await expect(page.getByRole('heading', { name: feiraName })).toBeVisible()
  await expect(page.getByText('2910800', { exact: true })).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?uf=PE')
  const caruaruTable = page.locator('table.data')
  await expect(caruaruTable.getByRole('link', { name: caruaruName })).toBeVisible()
  await expect(caruaruTable.getByRole('link', { name: feiraName })).toHaveCount(0)
  await expect(caruaruTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF PE/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/itens?uf=PE')
  await expect(page.getByText(/UF PE/).first()).toBeVisible()
  await expect(page.locator('table.data tbody tr').first()).toBeVisible()
  if (!againstCompose) {
    await expect(page.getByRole('link', { name: /Placa sinalizadora/ })).toBeVisible()
    await expect(page.getByText(/n=1/).first()).toBeVisible()
  }
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?municipioIbge=5201108')
  const anapolisTable = page.locator('table.data')
  await expect(anapolisTable.getByRole('link', { name: anapolisName })).toBeVisible()
  await expect(anapolisTable.getByRole('link', { name: vilaVelhaName })).toHaveCount(0)
  await expect(anapolisTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF GO/).first()).toBeVisible()
  await anapolisTable.getByRole('link', { name: anapolisName }).click()
  await expect(page.getByRole('heading', { name: anapolisName })).toBeVisible()
  await expect(page.getByText('5201108', { exact: true })).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?uf=ES')
  const vilaVelhaTable = page.locator('table.data')
  await expect(vilaVelhaTable.getByRole('link', { name: vilaVelhaName })).toBeVisible()
  await expect(vilaVelhaTable.getByRole('link', { name: anapolisName })).toHaveCount(0)
  await expect(vilaVelhaTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF ES/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/itens?uf=ES')
  await expect(page.getByText(/UF ES/).first()).toBeVisible()
  await expect(page.locator('table.data tbody tr').first()).toBeVisible()
  if (!againstCompose) {
    await expect(page.getByRole('link', { name: /Revelador Radiol/ })).toBeVisible()
    await expect(page.getByText(/n=1/).first()).toBeVisible()
  }
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?municipioIbge=2504009')
  const campinaTable = page.locator('table.data')
  await expect(campinaTable.getByRole('link', { name: campinaName })).toBeVisible()
  await expect(campinaTable.getByRole('link', { name: caucaiaName })).toHaveCount(0)
  await expect(campinaTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF PB/).first()).toBeVisible()
  await campinaTable.getByRole('link', { name: campinaName }).click()
  await expect(page.getByRole('heading', { name: campinaName })).toBeVisible()
  await expect(page.getByText('2504009', { exact: true })).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/orgaos?uf=CE')
  const caucaiaTable = page.locator('table.data')
  await expect(caucaiaTable.getByRole('link', { name: caucaiaName })).toBeVisible()
  await expect(caucaiaTable.getByRole('link', { name: campinaName })).toHaveCount(0)
  await expect(caucaiaTable.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(/UF CE/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/itens?uf=CE')
  await expect(page.getByText(/UF CE/).first()).toBeVisible()
  await expect(page.locator('table.data tbody tr').first()).toBeVisible()
  if (!againstCompose) {
    await expect(page.getByRole('link', { name: /Bloco receitu/ })).toBeVisible()
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

test('paginação preserva UF e IBGE', async ({ page }) => {
  await page.goto('/orgaos?uf=RJ&take=1')
  await expect(page.getByText(/UF RJ/).first()).toBeVisible()
  await expect(page.locator('table.data tbody tr')).toHaveCount(1)
  await page.getByRole('link', { name: 'Próxima' }).click()
  await expect(page).toHaveURL(/uf=RJ/)
  await expect(page).toHaveURL(/skip=1/)
  await expect(page.getByText(/UF RJ/).first()).toBeVisible()
  await expect(page.locator('table.data tbody a', { hasText: bauruName })).toHaveCount(0)
  await assertCoverageAndBan(page)

  await page.goto('/itens?uf=RJ&take=1')
  await expect(page.getByText(/UF RJ/).first()).toBeVisible()
  await page.getByRole('link', { name: 'Próxima' }).click()
  await expect(page).toHaveURL(/uf=RJ/)
  await expect(page.getByText(/UF RJ/).first()).toBeVisible()
  await expect(page.locator('table.data tbody tr')).toHaveCount(1)
  await assertCoverageAndBan(page)

  if (!againstCompose) {
    await page.goto('/orgaos?municipioIbge=3306305&take=1')
    await page.getByRole('link', { name: 'Próxima' }).click()
    await expect(page).toHaveURL(/municipioIbge=3306305/)
    await expect(page.getByText(/UF RJ/).first()).toBeVisible()
    await expect(page.locator('table.data tbody')).toContainText(/volta redonda/i)
    await expect(page.locator('table.data tbody a', { hasText: bauruName })).toHaveCount(0)
    await assertCoverageAndBan(page)
  }
})

test('unidade canônica e preço-base só quando o warehouse gravou', async ({ page }) => {
  if (againstCompose) {
    await page.goto('/itens?q=CONHECIDA')
    const unknownLink = page.locator('table.data tbody a').first()
    await expect(unknownLink).toBeVisible()
    await expect(page.locator('table.data tbody')).not.toHaveText(/unknown/i)
    await unknownLink.click()
  } else {
    await page.goto('/itens?q=Sinaliza')
    await expect(page.getByRole('link', { name: /Sinaliza/ })).toBeVisible()
    await expect(page.locator('table.data tbody')).not.toHaveText(/unknown/i)
    await page.getByRole('link', { name: /Sinaliza/ }).click()
    await expect(page.getByRole('heading', { name: /Sinaliza/ })).toBeVisible()
  }
  await expect(page.getByText('não mapeada').first()).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Valor por' })).toHaveCount(0)
  await expect(page.locator('body')).not.toHaveText(/\bunknown\b/)
  await assertCoverageAndBan(page)

  const mappedRow = page.locator('table.data tbody tr', { hasText: '·' }).first()
  await page.goto('/itens')
  await expect(mappedRow).toBeVisible()
  await mappedRow.locator('a').first().click()
  const mapped = page.locator('.fields div', { has: page.getByText('Unidade canônica', { exact: true }) })
  await expect(mapped.getByText('não mapeada')).toHaveCount(0)
  await expect(mapped.locator('dd')).not.toHaveText(/^n\/d$/)
  await expect(page.locator('.stats .kicker', { hasText: 'Valor por' })).toBeVisible()
  await expect(page.getByText(/R\$\s*[\d.]+,\d{2}/).first()).toBeVisible()
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
  await expect(page.getByText(/3170206/).first()).toBeVisible()
  await expect(page.getByText(/4113700/).first()).toBeVisible()
  await expect(page.getByText(/2910800/).first()).toBeVisible()
  await expect(page.getByText(/2604106/).first()).toBeVisible()
  await expect(page.getByText(/5201108/).first()).toBeVisible()
  await expect(page.getByText(/3205200/).first()).toBeVisible()
  await expect(page.getByText(/2504009/).first()).toBeVisible()
  await expect(page.getByText(/2303709/).first()).toBeVisible()
  await expect(page.getByText(/não é um total nacional/).first()).toBeVisible()
  await expect(page.getByText(/UF mista/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/metodologia')
  await expect(page.getByRole('heading', { name: /Metodologia/ })).toBeVisible()
  await assertCoverageAndBan(page)
})
