import { contratacoes, items, orgaos } from '@/lib/api/fixtures'
import {
  applyStoredAction,
  createStoredFlag,
  getStoredFlag,
  listStoredAudit,
  listStoredFlags,
} from '@/lib/api/flag-store'
import { emptyCoverage, fillCoverage, readCoverage } from '@/lib/coverage'
import {
  FLAG_FRAMING,
  isFlagState,
  summarizeFlagCounts,
  type CreateFlagBody,
  type DetectorKindCount,
  type FlagAction,
  type FlagAuditRecord,
  type FlagPage,
  type FlagQueueRow,
  type FlagRecord,
} from '@/lib/flags'
import { METHOD_VERSION } from '@/lib/copy'
import { ApiError, ApiNotFoundError, type Coverage } from '@/lib/types'

function usesStubApi(): boolean {
  const base = (process.env.API_BASE_URL ?? 'stub').trim()
  return base === '' || base === 'stub'
}

function apiRoot(): string {
  return (process.env.API_BASE_URL ?? 'stub').trim().replace(/\/$/, '')
}

function readFlag(raw: unknown): FlagRecord {
  if (!raw || typeof raw !== 'object') throw new ApiError(502, 'API sem indício')
  const o = raw as Record<string, unknown>
  const state = typeof o.state === 'string' && isFlagState(o.state) ? o.state : null
  if (!state || typeof o.id !== 'string' || typeof o.itemId !== 'string' || typeof o.kind !== 'string') {
    throw new ApiError(502, 'API devolveu indício inválido')
  }
  return {
    id: o.id,
    itemId: o.itemId,
    kind: o.kind,
    state,
    detectedAt: typeof o.detectedAt === 'string' ? o.detectedAt : '',
    notifiedAt: typeof o.notifiedAt === 'string' ? o.notifiedAt : null,
    notifyArtifact: typeof o.notifyArtifact === 'string' ? o.notifyArtifact : null,
    publishAfter: typeof o.publishAfter === 'string' ? o.publishAfter : null,
    publishedAt: typeof o.publishedAt === 'string' ? o.publishedAt : null,
    delta: typeof o.delta === 'string' ? o.delta : '',
    sourceUrl: typeof o.sourceUrl === 'string' ? o.sourceUrl : '',
    snapshotId: typeof o.snapshotId === 'string' ? o.snapshotId : '',
    methodologyVersion: typeof o.methodologyVersion === 'string' ? o.methodologyVersion : METHOD_VERSION,
    replyText: typeof o.replyText === 'string' ? o.replyText : null,
    repliedAt: typeof o.repliedAt === 'string' ? o.repliedAt : null,
    suspended: o.suspended === true,
    framing: typeof o.framing === 'string' ? o.framing : FLAG_FRAMING,
  }
}

async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiRoot()}${path}`, {
    ...init,
    headers: { accept: 'application/json', ...(init?.headers ?? {}) },
    cache: 'no-store',
  })
  if (res.status === 404) throw new ApiNotFoundError('indicio', path)
  if (!res.ok) {
    let detail = `API ${res.status} em ${path}`
    try {
      const body = (await res.json()) as { error?: string }
      if (body.error) detail = body.error
    } catch {
      // keep status text
    }
    throw new ApiError(res.status, detail)
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

function stubPage(flags: FlagRecord[], skip: number, take: number): FlagPage {
  const sliced = flags.slice(skip, skip + take)
  const coverage = fillCoverage(
    {
      n: flags.length,
      uf: null,
      quarter: null,
      methodologyVersion: METHOD_VERSION,
    },
    sliced,
  )
  return { items: sliced, total: flags.length, skip, take, coverage }
}

export async function listFlags(req: {
  skip: number
  take: number
  kind?: string
  state?: string
  itemId?: string
}): Promise<FlagPage> {
  if (usesStubApi()) return stubPage(listStoredFlags(req), req.skip, req.take)

  const params = new URLSearchParams()
  params.set('skip', String(req.skip))
  params.set('take', String(req.take))
  if (req.kind) params.set('kind', req.kind)
  if (req.state) params.set('state', req.state)
  if (req.itemId) params.set('itemId', req.itemId)
  const raw = await apiJson<Record<string, unknown>>(`/api/internal/flags?${params}`)
  const items = Array.isArray(raw.items) ? raw.items.map(readFlag) : []
  const coverage = readCoverage(raw.coverage)
  return {
    items,
    total: typeof raw.total === 'number' ? raw.total : coverage.n,
    skip: req.skip,
    take: req.take,
    coverage,
  }
}

export async function getFlag(id: string): Promise<FlagRecord> {
  if (usesStubApi()) return getStoredFlag(id)
  return readFlag(await apiJson<unknown>(`/api/internal/flags/${id}`))
}

export async function createFlag(body: CreateFlagBody): Promise<FlagRecord> {
  if (usesStubApi()) return createStoredFlag(body)
  return readFlag(
    await apiJson<unknown>('/api/internal/flags', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    }),
  )
}

const STAGING_NOTIFY_ARTIFACT = 'aviso-interno.txt'

export async function applyFlagAction(id: string, action: FlagAction): Promise<FlagRecord> {
  if (usesStubApi()) return applyStoredAction(id, action)
  return readFlag(
    await apiJson<unknown>(`/api/internal/flags/${id}/${action}`, {
      method: 'POST',
      headers: action === 'notify' ? { 'content-type': 'application/json' } : undefined,
      body: action === 'notify' ? JSON.stringify({ artifact: STAGING_NOTIFY_ARTIFACT }) : undefined,
    }),
  )
}

export async function listFlagAudit(id: string): Promise<FlagAuditRecord[]> {
  if (usesStubApi()) return listStoredAudit(id)
  try {
    const raw = await apiJson<{ items?: unknown[] }>(`/api/internal/flags/${id}/audit`)
    if (!Array.isArray(raw.items)) return []
    return raw.items.flatMap((row) => {
      if (!row || typeof row !== 'object') return []
      const o = row as Record<string, unknown>
      if (typeof o.toState !== 'string') return []
      return [
        {
          id: typeof o.id === 'string' ? o.id : `${o.toState}`,
          flagId: typeof o.flagId === 'string' ? o.flagId : id,
          fromState: typeof o.fromState === 'string' ? o.fromState : null,
          toState: o.toState,
          at: typeof o.at === 'string' ? o.at : '',
          actor: typeof o.actor === 'string' ? o.actor : 'internal/staging',
          reason: typeof o.reason === 'string' ? o.reason : null,
          delta: typeof o.delta === 'string' ? o.delta : null,
        },
      ]
    })
  } catch (err) {
    if (err instanceof ApiNotFoundError) throw err
    return []
  }
}

async function contextFor(itemId: string): Promise<{ itemDescricao: string; orgaoRazaoSocial: string }> {
  if (usesStubApi()) {
    const item = items.find((row) => row.id === itemId)
    const ct = item ? contratacoes.find((row) => row.id === item.contratacaoId) : undefined
    const orgao = ct ? orgaos.find((row) => row.id === ct.orgaoId) : undefined
    return {
      itemDescricao: item?.descricao ?? 'n/d',
      orgaoRazaoSocial: orgao?.razaoSocial ?? 'n/d',
    }
  }

  try {
    const raw = await apiJson<Record<string, unknown>>(`/api/items/${itemId}`)
    const wrapped = raw.item && typeof raw.item === 'object' ? (raw.item as Record<string, unknown>) : raw
    const descricao = typeof wrapped.descricao === 'string' ? wrapped.descricao : 'n/d'
    const orgao =
      typeof raw.orgaoRazaoSocial === 'string'
        ? raw.orgaoRazaoSocial
        : typeof wrapped.orgaoRazaoSocial === 'string'
          ? wrapped.orgaoRazaoSocial
          : 'n/d'
    return { itemDescricao: descricao, orgaoRazaoSocial: orgao }
  } catch {
    return { itemDescricao: 'n/d', orgaoRazaoSocial: 'n/d' }
  }
}

export async function enrichFlags(flags: FlagRecord[]): Promise<FlagQueueRow[]> {
  const unique = [...new Set(flags.map((flag) => flag.itemId))]
  const contexts = new Map(
    await Promise.all(unique.map(async (itemId) => [itemId, await contextFor(itemId)] as const)),
  )
  return flags.map((flag) => ({
    ...flag,
    itemDescricao: contexts.get(flag.itemId)?.itemDescricao ?? 'n/d',
    orgaoRazaoSocial: contexts.get(flag.itemId)?.orgaoRazaoSocial ?? 'n/d',
  }))
}

export async function listQueue(req: {
  skip: number
  take: number
  kind?: string
  state?: string
}): Promise<FlagPage & { rows: FlagQueueRow[] }> {
  const page = await listFlags(req)
  const rows = await enrichFlags(page.items)
  return { ...page, rows }
}

const FLAG_PAGE_TAKE = 100

export async function listFlagCounts(): Promise<{
  rows: DetectorKindCount[]
  coverage: Coverage
  total: number
}> {
  const first = await listFlags({ skip: 0, take: FLAG_PAGE_TAKE })
  const items = [...first.items]
  let skip = FLAG_PAGE_TAKE
  while (items.length < first.total) {
    const page = await listFlags({ skip, take: FLAG_PAGE_TAKE })
    if (page.items.length === 0) break
    items.push(...page.items)
    skip += FLAG_PAGE_TAKE
  }
  const coverage = {
    ...emptyCoverage(),
    ...first.coverage,
    n: first.total,
    uf: null,
  }
  return { rows: summarizeFlagCounts(items), coverage, total: first.total }
}
