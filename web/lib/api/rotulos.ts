import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { csvCol, csvEscape, parseCsvLine } from '@/lib/api/csv'
import type { LabelRubric } from '@/lib/flags'
import { ApiError } from '@/lib/types'
import {
  AGREEMENT_HEADER,
  emptyRotulosView,
  isPacketSlug,
  isRubric,
  KEY_FILE_MARK,
  ROTULOS_PACKETS,
  type BlindItem,
  type HumanLabelRow,
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

function assertSafeDataFile(root: string, file: string): string {
  const base = file.split(/[/\\]/).pop() ?? ''
  if (!base || base !== file || base.includes('..') || base.toLowerCase().includes(KEY_FILE_MARK)) {
    throw new Error('arquivo de pacote recusado')
  }
  const resolved = path.resolve(root, 'labels', 'adjudication', base)
  const allowedRoot = path.resolve(root, 'labels', 'adjudication')
  const rel = path.relative(allowedRoot, resolved)
  if (rel.startsWith('..') || path.isAbsolute(rel)) {
    throw new Error('arquivo de pacote recusado')
  }
  return resolved
}

function agreementPath(root: string, slug: RotulosPacketSlug): string {
  const resolved = path.resolve(root, 'labels', 'adjudication', 'agreement', `${slug}-human.csv`)
  const allowedRoot = path.resolve(root, 'labels', 'adjudication', 'agreement')
  const rel = path.relative(allowedRoot, resolved)
  if (rel.startsWith('..') || path.isAbsolute(rel)) {
    throw new Error('arquivo de acordo recusado')
  }
  return resolved
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

function viewAt(
  items: BlindItem[],
  labels: Map<string, HumanLabelRow>,
  index: number,
): RotulosView {
  const item = items[index]
  if (!item) {
    return {
      total: items.length,
      position: items.length,
      done: true,
      item: null,
      existingLabel: null,
      existingNotes: '',
    }
  }
  const existing = labels.get(item.packetRowId)
  return {
    total: items.length,
    position: index + 1,
    done: false,
    item,
    existingLabel: existing?.humanLabel ?? null,
    existingNotes: existing?.notes ?? '',
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
