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
const imperatrizName = /Munic[ií]pio de Imperatriz/i
const arapiracaName = /Munic[ií]pio de Arapiraca/i
const douradosName = /Dourados/i
const marabaName = /Munic[ií]pio de Marab[aá]/i
const varzeaName = /Munic[ií]pio de V[aá]rzea Grande/i
const jiParanaName = /Munic[ií]pio de Ji-Paran[aá]/i
const parnamirimName = /Munic[ií]pio de Parnamirim/i
const cruzeiroName = /Munic[ií]pio de Cruzeiro do Sul/i

const publishedNames = [
  niteroiName,
  bauruName,
  caxiasName,
  joinvilleName,
  uberlandiaName,
  londrinaName,
  feiraName,
  caruaruName,
  anapolisName,
  vilaVelhaName,
  campinaName,
  caucaiaName,
  imperatrizName,
  arapiracaName,
  douradosName,
  marabaName,
  varzeaName,
  jiParanaName,
  parnamirimName,
  cruzeiroName,
]

async function assertCoverageAndBan(page: Page) {
  await expect(page.getByText(/n=\d+/).first()).toBeVisible()
  await expect(page.getByText(/UF RJ|UF SP|UF RS|UF SC|UF MG|UF PR|UF BA|UF PE|UF GO|UF ES|UF PB|UF CE|UF MA|UF AL|UF MS|UF PA|UF MT|UF RO|UF RN|UF AC|UF mista|filtro sem registros/).first()).toBeVisible()
  await expect(page.getByText(/trimestre|trim\./i).first()).toBeVisible()
  await expect(page.getByText(/metodologia/i).first()).toBeVisible()
  await expect(page.locator('body')).not.toHaveText(banned)
  if (againstCompose) {
    await expect(page.locator('body')).not.toHaveText(stubLeak)
  }
}

async function assertOrgaoIbge(
  page: Page,
  ibge: string,
  present: RegExp,
  absent: RegExp,
  uf: string,
  heading: RegExp = present,
) {
  await page.goto(`/orgaos?municipioIbge=${ibge}`)
  const table = page.locator('table.data')
  await expect(table.getByRole('link', { name: present })).toBeVisible()
  await expect(table.getByRole('link', { name: absent })).toHaveCount(0)
  await expect(table.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(new RegExp(`UF ${uf}`)).first()).toBeVisible()
  await table.getByRole('link', { name: present }).click()
  await expect(page.getByRole('heading', { name: heading })).toBeVisible()
  await expect(page.getByText(ibge, { exact: true })).toBeVisible()
  await assertCoverageAndBan(page)
}

async function assertOrgaoUf(page: Page, uf: string, present: RegExp, absent: RegExp) {
  await page.goto(`/orgaos?uf=${uf}`)
  const table = page.locator('table.data')
  await expect(table.getByRole('link', { name: present })).toBeVisible()
  await expect(table.getByRole('link', { name: absent })).toHaveCount(0)
  await expect(table.getByRole('link', { name: voltaName })).toHaveCount(0)
  await expect(page.getByText(/n=1/).first()).toBeVisible()
  await expect(page.getByText(new RegExp(`UF ${uf}`)).first()).toBeVisible()
  await assertCoverageAndBan(page)
}

async function assertItensUf(page: Page, uf: string, stubName?: RegExp, stubN = '1') {
  await page.goto(`/itens?uf=${uf}`)
  await expect(page.getByText(new RegExp(`UF ${uf}`)).first()).toBeVisible()
  await expect(page.locator('table.data tbody tr').first()).toBeVisible()
  if (!againstCompose && stubName) {
    await expect(page.getByRole('link', { name: stubName })).toBeVisible()
    await expect(page.getByText(new RegExp(`n=${stubN}`)).first()).toBeVisible()
  }
  await assertCoverageAndBan(page)
}

test('home cards usam o n da coleção, não o n de itens', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('strong').filter({ hasText: 'Cobertura incompleta' })).toBeVisible()
  await expect(page.getByText(/UF mista/).first()).toBeVisible()
  await expect(page.getByText(/Caxias do Sul \(RS\), Joinville \(SC\), Uberlândia \(MG\), Londrina \(PR\), Feira de Santana \(BA\), Caruaru \(PE\), Anápolis \(GO\), Vila Velha \(ES\), Campina Grande \(PB\), Caucaia \(CE\), Imperatriz \(MA\), Arapiraca \(AL\), Dourados \(MS\), Marabá \(PA\), Várzea Grande \(MT\), Ji-Paraná \(RO\), Parnamirim \(RN\) e Cruzeiro do Sul \(AC\)/).first()).toBeVisible()
  const brand = page.locator('.brand-kicker')
  await expect(brand).toHaveText(/vinte e um municípios · 2024/i)
  await expect(brand).not.toHaveText(/Caxias do Sul|Uberlândia|Londrina|Feira de Santana|Caruaru|Anápolis|Vila Velha|Campina Grande|Caucaia|Imperatriz|Arapiraca|Dourados|Marabá|Várzea Grande|Ji-Paraná|Parnamirim|Cruzeiro do Sul/)
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
    await expect(orgaos.getByRole('strong')).toHaveText('24')
    await expect(itens.getByRole('strong')).toHaveText('48')
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
  await page.goto('/orgaos?take=50')
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

test('lista o recorte publicado com UF mista', async ({ page }) => {
  await page.goto('/orgaos?take=50')
  const publishedTable = page.locator('table.data')
  for (const name of publishedNames) {
    await expect(publishedTable.getByRole('link', { name })).toBeVisible()
  }
  await expect(page.getByText(/UF mista/).first()).toBeVisible()
  await assertCoverageAndBan(page)
})

test('filtra Niterói por IBGE no formulário', async ({ page }) => {
  await page.goto('/orgaos?take=50')
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
})

test('filtra Bauru por UF SP e itens SP', async ({ page }) => {
  await assertOrgaoUf(page, 'SP', bauruName, niteroiName)
  await assertItensUf(page, 'SP', /Papel A4 75 g/, '2')
})

test('filtra Caxias do Sul por IBGE e Joinville por UF SC', async ({ page }) => {
  await assertOrgaoIbge(page, '4305108', caxiasName, joinvilleName, 'RS')
  await assertOrgaoUf(page, 'SC', joinvilleName, caxiasName)
  await assertItensUf(page, 'SC', /Leitora c[oó]digo/)
})

test('filtra Uberlândia por IBGE e Londrina por UF PR', async ({ page }) => {
  await assertOrgaoIbge(page, '3170206', uberlandiaName, londrinaName, 'MG')
  await assertOrgaoUf(page, 'PR', londrinaName, uberlandiaName)
  await assertItensUf(page, 'PR', /Clindamicina/)
})

test('filtra Feira de Santana por IBGE e Caruaru por UF PE', async ({ page }) => {
  await assertOrgaoIbge(page, '2910800', feiraName, caruaruName, 'BA')
  await assertOrgaoUf(page, 'PE', caruaruName, feiraName)
  await assertItensUf(page, 'PE', /Placa sinalizadora/)
})

test('filtra Anápolis por IBGE e Vila Velha por UF ES', async ({ page }) => {
  await assertOrgaoIbge(page, '5201108', anapolisName, vilaVelhaName, 'GO')
  await assertOrgaoUf(page, 'ES', vilaVelhaName, anapolisName)
  await assertItensUf(page, 'ES', /Revelador Radiol/)
})

test('filtra Campina Grande por IBGE e Caucaia por UF CE', async ({ page }) => {
  await assertOrgaoIbge(page, '2504009', campinaName, caucaiaName, 'PB')
  await assertOrgaoUf(page, 'CE', caucaiaName, campinaName)
  await assertItensUf(page, 'CE', /Bloco receitu/)
})

test('filtra Imperatriz por IBGE e Arapiraca por UF AL', async ({ page }) => {
  await assertOrgaoIbge(page, '2105302', imperatrizName, arapiracaName, 'MA')
  await assertOrgaoUf(page, 'AL', arapiracaName, imperatrizName)
  await assertItensUf(page, 'AL', /Lamotrigina/)
})

test('filtra Dourados por IBGE e Marabá por UF PA', async ({ page }) => {
  await assertOrgaoIbge(page, '5003702', douradosName, marabaName, 'MS')
  await assertOrgaoUf(page, 'PA', marabaName, douradosName)
  await assertItensUf(page, 'PA', /Fog[aã]o/)
})

test('filtra Várzea Grande por IBGE e Ji-Paraná por UF RO', async ({ page }) => {
  await assertOrgaoIbge(page, '5108402', varzeaName, jiParanaName, 'MT')
  await assertOrgaoUf(page, 'RO', jiParanaName, varzeaName)
  await assertItensUf(page, 'RO', /Assinatura de banco/)
})

test('filtra Parnamirim por IBGE e Cruzeiro do Sul por UF AC', async ({ page }) => {
  await assertOrgaoIbge(page, '2403251', parnamirimName, cruzeiroName, 'RN')
  await assertOrgaoUf(page, 'AC', cruzeiroName, parnamirimName)
  await assertItensUf(page, 'AC', /Grade niveladora/)
})

test('mantém cobertura no filtro vazio e no vazio com UF', async ({ page }) => {
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
  await expect(page.getByText(/2105302/).first()).toBeVisible()
  await expect(page.getByText(/2700300/).first()).toBeVisible()
  await expect(page.getByText(/5003702/).first()).toBeVisible()
  await expect(page.getByText(/1504208/).first()).toBeVisible()
  await expect(page.getByText(/5108402/).first()).toBeVisible()
  await expect(page.getByText(/1100122/).first()).toBeVisible()
  await expect(page.getByText(/2403251/).first()).toBeVisible()
  await expect(page.getByText(/1200203/).first()).toBeVisible()
  await expect(page.getByText(/não é um total nacional/).first()).toBeVisible()
  await expect(page.getByText(/UF mista/).first()).toBeVisible()
  await assertCoverageAndBan(page)

  await page.goto('/metodologia')
  await expect(page.getByRole('heading', { name: /Metodologia/ })).toBeVisible()
  await assertCoverageAndBan(page)
})
