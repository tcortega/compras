import { expect, test } from '@playwright/test'

const againstCompose = Boolean(process.env.PLAYWRIGHT_BASE_URL)
const kinds = [
  'sanctioned_ceis_cnep',
  'cnpj_age',
  'cnpj_age_info',
  'fracionamento',
  'fracionamento_cluster',
  'retroactive_edit',
  'cnae_mismatch',
]
const bannedPublic = /fraude|corrupto|roubo|\bflag\b|ranking|adjacenc|shared_qsa|shared_partner|cover[_-]?bidd|bid_variance|winner_rotation|co[_-]?bid/i

test('cobertura interna conta por detector e fica fora do explorador', async ({ page, request }) => {
  await page.goto('/')
  await expect(page.locator('nav[aria-label="Seções"] a[href="/interno/cobertura"]')).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Rodapé"] a[href="/interno/cobertura"]')).toHaveCount(0)
  await expect(page.locator('body')).not.toHaveText(bannedPublic)

  await page.goto('/cobertura')
  await expect(page.getByRole('heading', { name: 'Cobertura incompleta' })).toBeVisible()
  for (const kind of kinds) {
    await expect(page.locator('body')).not.toHaveText(kind)
  }
  await expect(page.locator('nav[aria-label="Seções"] a[href="/interno/cobertura"]')).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Rodapé"] a[href="/interno/cobertura"]')).toHaveCount(0)
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)

  if (!againstCompose) {
    const itemLink = page.locator('table.data tbody a').first()
    await page.goto('/itens')
    await expect(itemLink).toBeVisible()
    const itemHref = await itemLink.getAttribute('href')
    expect(itemHref).toBeTruthy()
    const itemId = itemHref!.split('/').pop()
    const plant = await request.post('/api/interno/flags', {
      data: {
        itemId,
        kind: 'sanctioned_ceis_cnep',
        delta: 'Indício sintético de cruzamento CEIS/CNEP. Requer verificação.',
        sourceUrl: 'https://pncp.gov.br/app/editais/3306305/2024/1',
        snapshotId: 'sha256:coverage-counts-synthetic',
        methodologyVersion: '0.2',
      },
    })
    expect(plant.ok()).toBeTruthy()
  }

  await page.goto('/interno/cobertura')
  await expect(page.getByRole('heading', { name: 'Cobertura interna' })).toBeVisible()
  await expect(page.getByText('Contagens por detector').first()).toBeVisible()
  await expect(page.getByText(/n=\d+/).first()).toBeVisible()
  await expect(page.getByText(/UF mista|filtro sem registros/).first()).toBeVisible()
  await expect(page.getByText(/metodologia/i).first()).toBeVisible()
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Seções"] a[href="/interno/cobertura"]')).toHaveCount(0)
  await expect(page.locator('body')).not.toHaveText(bannedPublic)
  const table = page.locator('table.data')
  for (const kind of kinds) {
    await expect(table).toContainText(kind)
  }
  if (!againstCompose) {
    const planted = table.locator('tr', { hasText: 'sanctioned_ceis_cnep' })
    await expect(planted.locator('td').nth(1)).not.toHaveText('0')
  }
})
