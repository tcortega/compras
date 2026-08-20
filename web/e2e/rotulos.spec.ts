import { expect, test, type Page } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import { againstCompose } from './busca-helpers'
import {
  PEER_EMPTY,
  PEER_EXTRA,
  PEER_HEADING,
  ROTULOS_LEAK,
  SYNTHETIC_ITEMS,
  SYNTHETIC_PEERS,
  agreementFile,
  plantRotulosFixtures,
} from './rotulos-helpers'

const bannedPublic =
  /fraude|corrupto|roubo|\bflag\b|ranking|adjacenc|shared_qsa|shared_partner|cover[_-]?bidd|bid_variance|winner_rotation|co[_-]?bid|cnae_mismatch|hidden_label/i

const bannedRotulos = /hidden_label|cnae_mismatch|0\.99|\bscore\b|\brank\b|\bz\b|detector|fraude/i

const WHY =
  'O computador já marcou este preço como alto frente a itens semelhantes. Abra o link oficial. Depois escolha o porquê.'

const HINTS = [
  'Mesmo produto, mesmo pacote, e o preço oficial bate com a linha. Eles de fato pagaram isso.',
  'O tamanho do pacote não é o da comparação (ex.: isto é Pacote 10, os pares são 1 fita).',
  'Não é o mesmo produto do grupo de comparação.',
  'Não houve adjudicação de verdade, ou o número oficial não é o da linha (fracassado, deserto, cancelado, CSV errado).',
] as const

async function assertNoRotulosLink(page: Page) {
  await expect(page.locator('a[href="/interno/rotulos"]')).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Seções"] a[href="/interno/rotulos"]')).toHaveCount(0)
  await expect(page.locator('nav[aria-label="Rodapé"] a[href="/interno/rotulos"]')).toHaveCount(0)
}

function parseAgreement(text: string): Array<Record<string, string>> {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
  const header = lines[0]?.split(',') ?? []
  return lines.slice(1).map((line) => {
    const cols = line.split(',')
    const row: Record<string, string> = {}
    header.forEach((key, i) => {
      row[key] = cols[i] ?? ''
    })
    return row
  })
}

test('rotulos interno some do shell público, da cobertura e do explorador', async ({ page }) => {
  for (const path of ['/', '/cobertura', '/itens', '/interno/cobertura', '/interno/triagem']) {
    await page.goto(path)
    await assertNoRotulosLink(page)
  }
})

test('rotulos: worker confere três itens sintéticos e retoma no quarto', async ({ page }) => {
  if (againstCompose) {
    await page.goto('/interno/rotulos')
    await expect(page.getByText('Revisão interna')).toBeVisible()
    await expect(page.getByText('Conferir o item na fonte')).toBeVisible()
    await expect(page.getByText(WHY).first()).toBeVisible()
    await assertNoRotulosLink(page)
    await expect(page.locator('body')).not.toHaveText(bannedPublic)
    return
  }

  await plantRotulosFixtures()
  await page.goto('/interno/rotulos')
  await expect(page.getByText('1 de 4')).toBeVisible()
  await expect(page.getByRole('heading', { name: SYNTHETIC_ITEMS[0].descricao })).toBeVisible()
  await expect(page.getByText('vr-30 · Cidade Alfa · 2024')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Documento de origem' })).toHaveAttribute('target', '_blank')
  await expect(page.getByRole('link', { name: 'API do item' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Compra oficial' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Item oficial' })).toBeVisible()
  await expect(page.getByText(WHY)).toHaveCount(2)
  await expect(
    page.getByText('Conferir o item na fonte: compare unidade, quantidade e preço unitário, depois pressione 1 a 4.'),
  ).toHaveCount(2)
  for (const hint of HINTS) {
    await expect(page.getByText(hint)).toBeVisible()
  }
  await expect(page.getByRole('heading', { name: PEER_HEADING })).toBeVisible()
  await expect(page.getByText('Mediana do grupo')).toBeVisible()
  await expect(page.locator('.rotulos-peers-median')).toContainText(/18,40/)
  await expect(page.locator('.rotulos-peers-list li')).toHaveCount(3)
  for (const peer of SYNTHETIC_PEERS) {
    await expect(page.getByText(peer.descricao)).toBeVisible()
  }
  await expect(page.getByText(PEER_EMPTY)).toHaveCount(0)
  await expect(page.getByText(PEER_EXTRA)).toHaveCount(0)
  await expect(page.locator('body')).not.toHaveText(ROTULOS_LEAK)
  await expect(page.locator('body')).not.toHaveText(bannedPublic)
  await expect(page.locator('body')).not.toHaveText(bannedRotulos)
  await assertNoRotulosLink(page)

  await expect(page.getByRole('button', { name: 'Real' })).toBeEnabled()
  await page.keyboard.press('1')
  await expect(page.getByText('2 de 4')).toBeVisible()
  await expect(page.getByRole('heading', { name: SYNTHETIC_ITEMS[1].descricao })).toBeVisible()
  await expect(page.getByRole('heading', { name: PEER_HEADING })).toBeVisible()
  await expect(page.getByText(PEER_EMPTY)).toBeVisible()
  await expect(page.locator('.rotulos-peers-list')).toHaveCount(0)
  await expect(page.getByText('Mediana do grupo')).toHaveCount(0)
  await expect(page.getByText(SYNTHETIC_PEERS[0].descricao)).toHaveCount(0)

  await page.getByRole('button', { name: 'Voltar' }).click()
  await expect(page.getByText('1 de 4')).toBeVisible()
  await expect(page.getByRole('heading', { name: SYNTHETIC_ITEMS[0].descricao })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Real' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.locator('.rotulos-peers-list li')).toHaveCount(3)
  await expect(page.getByText(PEER_EMPTY)).toHaveCount(0)

  await page.keyboard.press('1')
  await expect(page.getByText('2 de 4')).toBeVisible()
  await page.getByLabel('Notas').fill('unidade conferida')
  await page.getByRole('button', { name: 'Erro de unidade' }).click()
  await expect(page.getByText('3 de 4')).toBeVisible()
  await expect(page.getByRole('heading', { name: SYNTHETIC_ITEMS[2].descricao })).toBeVisible()

  await page.getByRole('button', { name: 'Diferença de especificação' }).click()
  await expect(page.getByText('4 de 4')).toBeVisible()
  await expect(page.getByRole('heading', { name: SYNTHETIC_ITEMS[3].descricao })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Item oficial' })).toHaveCount(0)

  const saved = parseAgreement(await readFile(agreementFile(), 'utf8'))
  expect(saved).toHaveLength(3)
  expect(saved[0]).toMatchObject({
    packet_row_id: 'syn-row-001',
    packet: 'vr-30',
    city: 'Cidade Alfa',
    human_label: 'real',
  })
  expect(saved[1]).toMatchObject({
    packet_row_id: 'syn-row-002',
    human_label: 'unit error',
    notes: 'unidade conferida',
  })
  expect(saved[2]).toMatchObject({
    packet_row_id: 'syn-row-003',
    human_label: 'spec difference',
  })
  expect(saved.every((row) => /Z$/.test(row.labeled_at ?? ''))).toBeTruthy()

  await page.reload()
  await expect(page.getByText('4 de 4')).toBeVisible()
  await expect(page.getByRole('heading', { name: SYNTHETIC_ITEMS[3].descricao })).toBeVisible()
  await expect(page.getByRole('heading', { name: PEER_HEADING })).toBeVisible()
  await expect(page.getByText(PEER_EMPTY)).toBeVisible()
  await expect(page.locator('body')).not.toHaveText(ROTULOS_LEAK)
  await expect(page.locator('body')).not.toHaveText(bannedPublic)
  await expect(page.locator('body')).not.toHaveText(bannedRotulos)
})
