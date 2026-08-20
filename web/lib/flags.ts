import type { Coverage } from '@/lib/types'

export const FLAG_STATES = [
  'detected',
  'internal_review',
  'notified',
  'published',
  'resolved',
  'retracted',
] as const

export type FlagState = (typeof FLAG_STATES)[number]

export const FLAG_FRAMING = 'indicio requiring verification'

export const TRIAGE_KIND = 'triage_synthetic'

export const LABEL_RUBRIC = [
  { value: 'real', label: 'Real' },
  { value: 'unit error', label: 'Erro de unidade' },
  { value: 'spec difference', label: 'Diferença de especificação' },
  { value: 'data error', label: 'Erro de dado' },
] as const

export type LabelRubric = (typeof LABEL_RUBRIC)[number]['value']

export type FlagRecord = {
  id: string
  itemId: string
  kind: string
  state: FlagState
  detectedAt: string
  notifiedAt: string | null
  notifyArtifact: string | null
  publishAfter: string | null
  publishedAt: string | null
  delta: string
  sourceUrl: string
  snapshotId: string
  methodologyVersion: string
  replyText: string | null
  repliedAt: string | null
  suspended: boolean
  framing: string
}

export type FlagAuditRecord = {
  id: string
  flagId: string
  fromState: string | null
  toState: string
  at: string
  actor: string
  reason: string | null
  delta: string | null
}

export type FlagPage = {
  items: FlagRecord[]
  total: number
  skip: number
  take: number
  coverage: Coverage
}

export type FlagQueueRow = FlagRecord & {
  itemDescricao: string
  orgaoRazaoSocial: string
}

export type CreateFlagBody = {
  itemId: string
  kind: string
  delta: string
  sourceUrl: string
  snapshotId: string
  methodologyVersion: string
}

export type FlagAction = 'review' | 'notify' | 'publish' | 'resolve' | 'retract'

export const STATE_LABEL: Record<FlagState, string> = {
  detected: 'Detectado',
  internal_review: 'Revisão interna',
  notified: 'Notificado',
  published: 'Publicado',
  resolved: 'Resolvido',
  retracted: 'Retratado',
}

export const ACTION_LABEL: Record<FlagAction, string> = {
  review: 'Revisar',
  notify: 'Notificar órgão',
  publish: 'Publicar',
  resolve: 'Resolver',
  retract: 'Retratar',
}

export function isFlagState(raw: string | undefined): raw is FlagState {
  return raw != null && (FLAG_STATES as readonly string[]).includes(raw)
}

export function actionsFor(state: FlagState): FlagAction[] {
  if (state === 'detected') return ['review']
  if (state === 'internal_review') return ['notify']
  if (state === 'notified') return ['publish']
  if (state === 'published') return ['resolve', 'retract']
  return []
}

export const DETECTOR_KINDS = [
  'sanctioned_ceis_cnep',
  'cnpj_age',
  'cnpj_age_info',
  'fracionamento',
  'fracionamento_cluster',
  'retroactive_edit',
  'cnae_mismatch',
] as const

export type DetectorKindCount = {
  id: string
  kind: string
  n: number
  day: string | null
}

function detectedDay(iso: string): string | null {
  const match = /^(\d{4}-\d{2}-\d{2})/.exec(iso)
  return match?.[1] ?? null
}

export function summarizeFlagCounts(flags: FlagRecord[]): DetectorKindCount[] {
  const buckets = new Map<string, { kind: string; day: string | null; n: number }>()
  for (const flag of flags) {
    const day = detectedDay(flag.detectedAt)
    const key = `${flag.kind}\t${day ?? ''}`
    const cur = buckets.get(key)
    if (cur) cur.n += 1
    else buckets.set(key, { kind: flag.kind, day, n: 1 })
  }
  const days = new Set(
    [...buckets.values()].flatMap((row) => (row.day ? [row.day] : [])),
  )
  const byDay = days.size > 1
  const rows: DetectorKindCount[] = []
  const seen = new Set<string>()
  if (byDay) {
    for (const row of buckets.values()) {
      const id = row.day ? `${row.kind}:${row.day}` : row.kind
      rows.push({ id, kind: row.kind, n: row.n, day: row.day })
      seen.add(row.kind)
    }
  } else {
    const last = new Map<string, DetectorKindCount>()
    for (const row of buckets.values()) {
      const cur = last.get(row.kind)
      if (!cur) last.set(row.kind, { id: row.kind, kind: row.kind, n: row.n, day: row.day })
      else {
        cur.n += row.n
        if (row.day && (!cur.day || row.day > cur.day)) cur.day = row.day
      }
    }
    for (const row of last.values()) {
      rows.push(row)
      seen.add(row.kind)
    }
  }
  for (const kind of DETECTOR_KINDS) {
    if (!seen.has(kind)) rows.push({ id: kind, kind, n: 0, day: null })
  }
  return rows.sort((a, b) => a.kind.localeCompare(b.kind, 'pt-BR') || (a.day ?? '').localeCompare(b.day ?? ''))
}

export const triageCopy = {
  kicker: 'Fila interna',
  title: 'Triagem de indícios',
  lede: 'Cada linha é um indício a verificar. Esta rota não é pública e não publica alertas no explorador.',
  framing: 'Indício a verificar',
  hold: 'O órgão é notificado 7 dias antes de qualquer publicação.',
  precision: 'A precisão da Fase 0 é 9%. Alertas públicos permanecem fechados.',
  empty: 'Nenhum indício neste filtro.',
  holdConflict: 'A carência de 7 dias ainda não passou.',
  transitionConflict: 'Não foi possível aplicar a transição.',
  labeled: 'Rótulo gravado em triage-labels.csv.',
  evidence: 'Documento de origem',
  notifyArtifact: 'Registro de aviso',
  audit: 'Trilha de estados',
  timestamps: 'Marcas de tempo',
  labels: 'Rótulo da rubrica',
  notes: 'Notas',
} as const

export const coberturaInternaCopy = {
  kicker: 'Recorte interno',
  title: 'Cobertura interna',
  lede: 'Contagens por detector no warehouse. Esta rota não é pública e não publica alertas no explorador.',
  kinds: 'Contagens por detector',
  day: 'Dia da última rodada',
  emptyDay: 'sem rodada',
  framing: 'Indício a verificar',
} as const
