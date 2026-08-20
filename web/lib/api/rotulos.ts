import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { csvCol, csvEscape, parseCsvLine } from '@/lib/api/csv'
import type { LabelRubric } from '@/lib/flags'
import { ApiError } from '@/lib/types'
import {
  AGREEMENT_HEADER,
  emptyPeerGroup,
  emptyRotulosView,
  isPacketSlug,
  isRubric,
  KEY_FILE_MARK,
  ROTULOS_PACKETS,
  ROTULOS_PEER_LIMIT,
  type BlindItem,
  type HumanLabelRow,
  type PeerGroup,
  type PeerPurchase,
  type RotulosPacketSlug,
  type RotulosView,
} from '@/lib/rotulos'

let writeChain: Promise<unknown> = Promise.resolve()

function withWriteLock<T>(fn: () => Promise<T>): Promise<T> {
  const run = writeChain.then(fn, fn)
  writeChain = run.then(
    () => undefined,
    () => undefined,
  )
  return run
}

export function comprasDataDir(): string | null {
  const raw = process.env.COMPRAS_DATA_DIR?.trim()
  if (!raw) return null
  return path.resolve(raw)
}

function assertInside(allowedRoot: string, resolved: string, message: string): string {
  const rel = path.relative(allowedRoot, resolved)
  if (rel.startsWith('..') || path.isAbsolute(rel) || resolved.toLowerCase().includes(KEY_FILE_MARK)) {
    throw new Error(message)
  }
  return resolved
}

function assertSafeBase(file: string, message: string): string {
  const base = file.split(/[/\\]/).pop() ?? ''
  if (!base || base !== file || base.includes('..') || base.toLowerCase().includes(KEY_FILE_MARK)) {
    throw new Error(message)
  }
  return base
}

function assertSafeDataFile(root: string, file: string): string {
  const base = assertSafeBase(file, 'arquivo de pacote recusado')
  return assertInside(
    path.resolve(root, 'labels', 'adjudication'),
    path.resolve(root, 'labels', 'adjudication', base),
    'arquivo de pacote recusado',
  )
}

function agreementPath(root: string, slug: RotulosPacketSlug): string {
  return assertInside(
    path.resolve(root, 'labels', 'adjudication', 'agreement'),
    path.resolve(root, 'labels', 'adjudication', 'agreement', `${slug}-human.csv`),
    'arquivo de acordo recusado',
  )
}

function peersPath(root: string, slug: RotulosPacketSlug): string {
  const file = assertSafeBase(`${slug}-peers.json`, 'arquivo de pares recusado')
  return assertInside(
    path.resolve(root, 'labels', 'adjudication', 'peers'),
    path.resolve(root, 'labels', 'adjudication', 'peers', file),
    'arquivo de pares recusado',
  )
}

function toItem(packet: RotulosPacketSlug, headers: string[], row: string[]): BlindItem | null {
  const packetRowId = csvCol(row, headers, 'packet_row_id')
  if (!packetRowId) return null
  return {
    packet,
    packetRowId,
    city: csvCol(row, headers, 'city'),
    ibge: csvCol(row, headers, 'ibge'),
    year: csvCol(row, headers, 'year'),
    idCompra: csvCol(row, headers, 'id_compra'),
    idCompraItem: csvCol(row, headers, 'id_compra_item'),
    idContratacaoPncp: csvCol(row, headers, 'ID_contratacao_PNCP'),
    numeroItem: csvCol(row, headers, 'numero_item'),
    descricao: csvCol(row, headers, 'descricao'),
    unidadeMedida: csvCol(row, headers, 'unidade_medida'),
    quantidade: csvCol(row, headers, 'quantidade'),
    valorUnitarioEstimado: csvCol(row, headers, 'valor_unitario_estimado'),
    valorUnitarioResultado: csvCol(row, headers, 'valor_unitario_resultado'),
    valorTotal: csvCol(row, headers, 'valor_total'),
    valorTotalResultado: csvCol(row, headers, 'valor_total_resultado'),
    catalogCode: csvCol(row, headers, 'catalog_code'),
    sourceDocUrl: csvCol(row, headers, 'source_doc_url'),
    pncpItemApiUrl: csvCol(row, headers, 'pncp_item_api_url'),
    officialCompraUrl: csvCol(row, headers, 'official_compra_url'),
    officialItemUrl: csvCol(row, headers, 'official_item_url'),
  }
}

async function readCsvRows(file: string): Promise<string[][]> {
  let text = ''
  try {
    text = await readFile(file, 'utf8')
  } catch {
    return []
  }
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map(parseCsvLine)
}

export async function loadBlindItems(): Promise<BlindItem[]> {
  const root = comprasDataDir()
  if (!root) return []
  const items: BlindItem[] = []
  for (const packet of ROTULOS_PACKETS) {
    const file = assertSafeDataFile(root, packet.file)
    const rows = await readCsvRows(file)
    const header = rows[0]
    if (!header) continue
    for (const row of rows.slice(1)) {
      const item = toItem(packet.slug, header, row)
      if (item) items.push(item)
    }
  }
  return items
}

function parseHumanRow(headers: string[], row: string[]): HumanLabelRow | null {
  const packetRowId = csvCol(row, headers, 'packet_row_id')
  const packet = csvCol(row, headers, 'packet')
  const humanLabel = csvCol(row, headers, 'human_label')
  if (!packetRowId || !isPacketSlug(packet) || !isRubric(humanLabel)) return null
  return {
    packetRowId,
    packet,
    city: csvCol(row, headers, 'city'),
    ibge: csvCol(row, headers, 'ibge'),
    year: csvCol(row, headers, 'year'),
    idCompraItem: csvCol(row, headers, 'id_compra_item'),
    idContratacaoPncp: csvCol(row, headers, 'ID_contratacao_PNCP'),
    numeroItem: csvCol(row, headers, 'numero_item'),
    humanLabel,
    notes: csvCol(row, headers, 'notes'),
    labeledAt: csvCol(row, headers, 'labeled_at'),
  }
}

export async function loadHumanLabels(): Promise<Map<string, HumanLabelRow>> {
  const root = comprasDataDir()
  const out = new Map<string, HumanLabelRow>()
  if (!root) return out
  for (const packet of ROTULOS_PACKETS) {
    const file = agreementPath(root, packet.slug)
    const rows = await readCsvRows(file)
    const header = rows[0]
    if (!header) continue
    for (const row of rows.slice(1)) {
      const parsed = parseHumanRow(header, row)
      if (parsed) out.set(parsed.packetRowId, parsed)
    }
  }
  return out
}

function parsePeerPurchase(raw: unknown): PeerPurchase | null {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null
  const row = raw as Record<string, unknown>
  const descricao = typeof row.descricao === 'string' ? row.descricao.trim() : ''
  const unidadeMedida = typeof row.unidade_medida === 'string' ? row.unidade_medida.trim() : ''
  const valorUnitario = typeof row.valor_unitario === 'string' ? row.valor_unitario.trim() : ''
  if (!descricao && !unidadeMedida && !valorUnitario) return null
  return { descricao, unidadeMedida, valorUnitario }
}

function parsePeerGroup(raw: unknown): PeerGroup {
  const empty = emptyPeerGroup()
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return empty
  const rec = raw as Record<string, unknown>
  if (!Array.isArray(rec.peers)) return empty
  const peers: PeerPurchase[] = []
  for (const row of rec.peers) {
    const peer = parsePeerPurchase(row)
    if (!peer) continue
    peers.push(peer)
    if (peers.length >= ROTULOS_PEER_LIMIT) break
  }
  if (peers.length === 0) return empty
  const medianUnitPrice = typeof rec.median_unit_price === 'string' ? rec.median_unit_price.trim() : ''
  return { medianUnitPrice, peers }
}

async function loadPeerGroup(packet: RotulosPacketSlug, packetRowId: string): Promise<PeerGroup> {
  const empty = emptyPeerGroup()
  const root = comprasDataDir()
  if (!root) return empty
  try {
    const file = peersPath(root, packet)
    const parsed = JSON.parse(await readFile(file, 'utf8')) as unknown
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return empty
    const rec = parsed as Record<string, unknown>
    if (!Object.hasOwn(rec, packetRowId)) return empty
    return parsePeerGroup(rec[packetRowId])
  } catch {
    return empty
  }
}

async function viewAt(
  items: BlindItem[],
  labels: Map<string, HumanLabelRow>,
  index: number,
): Promise<RotulosView> {
  const item = items[index]
  if (!item) {
    return {
      total: items.length,
      position: items.length,
      done: true,
      item: null,
      existingLabel: null,
      existingNotes: '',
      ...emptyPeerGroup(),
    }
  }
  const existing = labels.get(item.packetRowId)
  const peers = await loadPeerGroup(item.packet, item.packetRowId)
  return {
    total: items.length,
    position: index + 1,
    done: false,
    item,
    existingLabel: existing?.humanLabel ?? null,
    existingNotes: existing?.notes ?? '',
    ...peers,
  }
}

function firstUnlabeledIndex(items: BlindItem[], labels: Map<string, HumanLabelRow>, after = -1): number {
  for (let i = after + 1; i < items.length; i += 1) {
    const id = items[i]?.packetRowId
    if (id && !labels.has(id)) return i
  }
  return -1
}

export async function loadRotulosView(at?: number): Promise<RotulosView> {
  const items = await loadBlindItems()
  if (items.length === 0) return emptyRotulosView()
  const labels = await loadHumanLabels()
  if (at != null && Number.isFinite(at)) {
    if (at < 1) return viewAt(items, labels, 0)
    if (at > items.length) return viewAt(items, labels, items.length)
    return viewAt(items, labels, at - 1)
  }
  const next = firstUnlabeledIndex(items, labels)
  if (next < 0) return viewAt(items, labels, items.length)
  return viewAt(items, labels, next)
}

function serializeHuman(row: HumanLabelRow): string {
  return [
    csvEscape(row.packetRowId),
    csvEscape(row.packet),
    csvEscape(row.city),
    csvEscape(row.ibge),
    csvEscape(row.year),
    csvEscape(row.idCompraItem),
    csvEscape(row.idContratacaoPncp),
    csvEscape(row.numeroItem),
    csvEscape(row.humanLabel),
    csvEscape(row.notes),
    csvEscape(row.labeledAt),
  ].join(',')
}

async function upsertHumanLabel(row: HumanLabelRow): Promise<HumanLabelRow> {
  const root = comprasDataDir()
  if (!root) throw new ApiError(400, 'COMPRAS_DATA_DIR ausente')
  const file = agreementPath(root, row.packet)
  await mkdir(path.dirname(file), { recursive: true })
  const rows = await readCsvRows(file)
  const header = rows[0] ?? parseCsvLine(AGREEMENT_HEADER)
  const next: HumanLabelRow[] = []
  let replaced = false
  for (const raw of rows.slice(1)) {
    const parsed = parseHumanRow(header, raw)
    if (!parsed) continue
    if (parsed.packetRowId === row.packetRowId) {
      next.push(row)
      replaced = true
    } else {
      next.push(parsed)
    }
  }
  if (!replaced) next.push(row)
  const body = `${AGREEMENT_HEADER}\n${next.map(serializeHuman).join('\n')}\n`
  await writeFile(file, body, 'utf8')
  return row
}

export async function saveRotulosLabel(input: {
  packetRowId: string
  humanLabel: LabelRubric
  notes: string
}): Promise<RotulosView> {
  return withWriteLock(async () => {
    const items = await loadBlindItems()
    const current = items.find((row) => row.packetRowId === input.packetRowId)
    if (!current) throw new ApiError(400, 'item ausente no pacote')
    const labeledAt = new Date().toISOString()
    await upsertHumanLabel({
      packetRowId: current.packetRowId,
      packet: current.packet,
      city: current.city,
      ibge: current.ibge,
      year: current.year,
      idCompraItem: current.idCompraItem,
      idContratacaoPncp: current.idContratacaoPncp,
      numeroItem: current.numeroItem,
      humanLabel: input.humanLabel,
      notes: input.notes.trim(),
      labeledAt,
    })
    const labels = await loadHumanLabels()
    const currentIndex = items.findIndex((row) => row.packetRowId === current.packetRowId)
    const next = firstUnlabeledIndex(items, labels, currentIndex)
    if (next < 0) {
      const wrap = firstUnlabeledIndex(items, labels)
      if (wrap < 0) return viewAt(items, labels, items.length)
      return viewAt(items, labels, wrap)
    }
    return viewAt(items, labels, next)
  })
}
