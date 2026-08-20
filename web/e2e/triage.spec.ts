import { expect, test } from '@playwright/test'

const bannedPublic = /fraude|corrupto|roubo|\bflag\b|ranking|adjacenc|shared_qsa|shared_partner/i

test('triagem interna caminha detectado, revisão e notificação sem publicar', async ({ page, request }) => {
  await page.goto('/itens')
  const itemLink = page.locator('table.data tbody a').first()
  await expect(itemLink).toBeVisible()
  const itemName = (await itemLink.innerText()).trim()
  const itemHref = await itemLink.getAttribute('href')
  expect(itemHref).toBeTruthy()
  const itemId = itemHref!.split('/').pop()
  expect(itemId).toBeTruthy()

  const plant = await request.post('/api/interno/flags', {
    data: {
      itemId,
      kind: 'triage_synthetic',
      delta: 'Indício sintético para triagem. Requer verificação.',
      sourceUrl: 'https://pncp.gov.br/app/editais/3306305/2024/1',
      snapshotId: 'sha256:triage-synthetic',
      methodologyVersion: '0.1',
    },
  })
  expect(plant.ok()).toBeTruthy()
  const created = (await plant.json()) as { id: string; state: string; framing: string }
  expect(created.state).toBe('detected')
  expect(created.framing).toBe('indicio requiring verification')

  await page.goto('/')
  await expect(page.locator('nav[aria-label="Seções"] a[href="/interno/triagem"]')).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Rodapé"] a[href="/interno/triagem"]')).toHaveCount(0)
  await expect(page.locator('body')).not.toHaveText(bannedPublic)

  await page.goto('/interno/triagem?kind=triage_synthetic&state=detected')
  await expect(page.getByRole('heading', { name: 'Triagem de indícios' })).toBeVisible()
  await expect(page.getByText('Indício a verificar').first()).toBeVisible()
  await expect(page.locator('table.data tbody')).toContainText('triage_synthetic')
  await expect(page.locator('table.data tbody')).toContainText(/detectado/i)
  await expect(page.locator('table.data tbody')).toContainText(itemName)
  await expect(page.getByRole('link', { name: 'Documento de origem' }).first()).toBeVisible()
  await expect(page.locator('nav[aria-label="Seções"] a[href="/interno/triagem"]')).toHaveCount(0)
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)

  await page.getByRole('link', { name: itemName }).first().click()
  await expect(page.getByRole('heading', { name: itemName })).toBeVisible()
  await expect(page.getByText('Indício a verificar').first()).toBeVisible()
  await expect(page.getByText('criação para Detectado')).toBeVisible()

  await page.getByRole('button', { name: 'Revisar' }).click()
  await expect(page.getByText('Revisão interna').first()).toBeVisible()
  await expect(page.getByText('Detectado para Revisão interna')).toBeVisible()

  await page.getByRole('button', { name: 'Notificar órgão' }).click()
  await expect(page.locator('.fields div', { has: page.getByText('Estado', { exact: true }) })).toContainText(
    'Notificado',
  )
  await expect(page.getByText('Revisão interna para Notificado')).toBeVisible()

  await page.getByRole('button', { name: 'Publicar' }).click()
  await expect(page.getByText('A carência de 7 dias ainda não passou.')).toBeVisible()
  await expect(page.locator('.fields div', { has: page.getByText('Estado', { exact: true }) })).toContainText(
    'Notificado',
  )

  await page.getByRole('button', { name: 'Erro de unidade' }).click()
  await expect(page.getByText('Rótulo gravado em triage-labels.csv.')).toBeVisible()
  const labels = await request.get('/api/interno/labels')
  expect(labels.ok()).toBeTruthy()
  const labeled = (await labels.json()) as { items: Array<{ flag_id: string; label: string }> }
  expect(labeled.items.some((row) => row.flag_id === created.id && row.label === 'unit error')).toBeTruthy()

  await page.goto(itemHref!)
  await expect(page.getByRole('heading', { name: itemName })).toBeVisible()
  await expect(page.locator('body')).not.toHaveText(bannedPublic)
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)

  await page.goto('/orgaos')
  await expect(page.locator('body')).not.toHaveText(bannedPublic)
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Seções"] a[href="/interno/triagem"]')).toHaveCount(0)

  await page.goto('/fornecedores')
  await expect(page.locator('body')).not.toHaveText(bannedPublic)
  await page.locator('table.data tbody a').first().click()
  await expect(page.locator('.stats .kicker', { hasText: 'Homologado' })).toHaveCount(0)
  await expect(page.locator('body')).not.toHaveText(bannedPublic)
})
