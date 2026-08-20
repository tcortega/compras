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

export const triageCopy = {
  kicker: 'Fila interna',
  title: 'Triagem de indícios',
  lede: 'Cada linha é um indício a verificar. Esta rota não é pública e não publica alertas no explorador.',
  framing: 'Indício a verificar',
  hold: 'O órgão é notificado 7 dias antes de qualquer publicação.',
  precision: 'A precisão da Fase 0 é 9%. Alertas públicos permanecem fechados.',
  empty: 'Nenhum indício neste filtro.',
  holdConflict: 'A carência de 7 dias ainda não passou.',
  labeled: 'Rótulo gravado em triage-labels.csv.',
  evidence: 'Documento de origem',
  audit: 'Trilha de estados',
  timestamps: 'Marcas de tempo',
  labels: 'Rótulo da rubrica',
  notes: 'Notas',
} as const
