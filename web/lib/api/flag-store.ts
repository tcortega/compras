import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { ApiError, ApiNotFoundError } from '@/lib/types'
import { FLAG_FRAMING, type CreateFlagBody, type FlagAction, type FlagAuditRecord, type FlagRecord } from '@/lib/flags'

type Stored = {
  flag: FlagRecord
  audit: FlagAuditRecord[]
}

function storePath(): string {
  return process.env.TRIAGE_FLAGS_PATH?.trim() || path.join('/tmp', 'compras-triage-flags.json')
}

function load(): Map<string, Stored> {
  try {
    const raw = JSON.parse(readFileSync(storePath(), 'utf8')) as Stored[]
    return new Map(raw.map((row) => [row.flag.id, row]))
  } catch {
    return new Map()
  }
}

function save(rows: Map<string, Stored>): void {
  const file = storePath()
  mkdirSync(path.dirname(file), { recursive: true })
  writeFileSync(file, JSON.stringify([...rows.values()]), 'utf8')
}

function nowIso(): string {
  return new Date().toISOString()
}

function addDays(iso: string, days: number): string {
  return new Date(new Date(iso).getTime() + days * 24 * 60 * 60 * 1000).toISOString()
}

function writeAudit(stored: Stored, fromState: string | null, toState: string, at: string, delta?: string | null) {
  stored.audit.push({
    id: `${stored.audit.length + 1}`,
    flagId: stored.flag.id,
    fromState,
    toState,
    at,
    actor: 'internal/staging',
    reason: null,
    delta: delta ?? null,
  })
}

export function listStoredFlags(filter: { kind?: string; state?: string; itemId?: string }): FlagRecord[] {
  return [...load().values()]
    .map((row) => row.flag)
    .filter((flag) => !filter.kind || flag.kind === filter.kind)
    .filter((flag) => !filter.state || flag.state === filter.state)
    .filter((flag) => !filter.itemId || flag.itemId === filter.itemId)
    .sort((a, b) => a.kind.localeCompare(b.kind, 'pt-BR') || a.itemId.localeCompare(b.itemId) || a.id.localeCompare(b.id))
}

export function getStoredFlag(id: string): FlagRecord {
  const row = load().get(id)
  if (!row) throw new ApiNotFoundError('indicio', id)
  return row.flag
}

export function listStoredAudit(id: string): FlagAuditRecord[] {
  const row = load().get(id)
  if (!row) throw new ApiNotFoundError('indicio', id)
  return row.audit
}

export function createStoredFlag(body: CreateFlagBody): FlagRecord {
  if (!body.itemId || !body.kind || !body.delta || !body.sourceUrl || !body.snapshotId || !body.methodologyVersion) {
    throw new ApiError(400, 'Pedido inválido')
  }
  const at = nowIso()
  const flag: FlagRecord = {
    id: crypto.randomUUID(),
    itemId: body.itemId,
    kind: body.kind,
    state: 'detected',
    detectedAt: at,
    notifiedAt: null,
    notifyArtifact: null,
    publishAfter: null,
    publishedAt: null,
    delta: body.delta,
    sourceUrl: body.sourceUrl,
    snapshotId: body.snapshotId,
    methodologyVersion: body.methodologyVersion,
    replyText: null,
    repliedAt: null,
    suspended: false,
    framing: FLAG_FRAMING,
  }
  const stored: Stored = { flag, audit: [] }
  writeAudit(stored, null, 'detected', at, body.delta)
  const rows = load()
  rows.set(flag.id, stored)
  save(rows)
  return flag
}

export function applyStoredAction(id: string, action: FlagAction): FlagRecord {
  const rows = load()
  const stored = rows.get(id)
  if (!stored) throw new ApiNotFoundError('indicio', id)
  const at = nowIso()
  const from = stored.flag.state
  const next = transition(stored.flag, action, at)
  stored.flag = next
  writeAudit(stored, from, next.state, at)
  save(rows)
  return next
}

function transition(flag: FlagRecord, action: FlagAction, at: string): FlagRecord {
  if (action === 'review') {
    if (flag.state !== 'detected') throw new ApiError(409, 'O indício não está em detectado.')
    return { ...flag, state: 'internal_review' }
  }
  if (action === 'notify') {
    if (flag.state !== 'internal_review') throw new ApiError(409, 'O indício não está em revisão interna.')
    return {
      ...flag,
      state: 'notified',
      notifiedAt: at,
      publishAfter: addDays(at, 7),
      notifyArtifact: 'aviso-interno.txt',
    }
  }
  if (action === 'publish') {
    if (flag.state !== 'notified') throw new ApiError(409, 'O indício não está em notificado.')
    if (!flag.publishAfter || Date.now() < new Date(flag.publishAfter).getTime()) {
      throw new ApiError(409, 'Notify hold has not elapsed.')
    }
    if (flag.suspended) throw new ApiError(409, 'O indício está suspenso.')
    return { ...flag, state: 'published', publishedAt: at }
  }
  if (action === 'resolve') {
    if (flag.state !== 'published') throw new ApiError(409, 'O indício não está em publicado.')
    return { ...flag, state: 'resolved' }
  }
  if (action === 'retract') {
    if (flag.state !== 'published') throw new ApiError(409, 'O indício não está em publicado.')
    return { ...flag, state: 'retracted' }
  }
  throw new ApiError(400, 'Pedido inválido')
}
