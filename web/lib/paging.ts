import type { Esfera, PageRequest } from '@/lib/types'

export const DEFAULT_TAKE = 20
export const MAX_TAKE = 100

function first(
  value: string | string[] | undefined,
): string | undefined {
  if (Array.isArray(value)) return value[0]
  return value
}

function intOr(raw: string | undefined, fallback: number, min: number, max: number): number {
  if (raw == null || raw === '') return fallback
  const n = Number.parseInt(raw, 10)
  if (!Number.isFinite(n)) return fallback
  return Math.min(max, Math.max(min, n))
}

const ESFERAS = new Set<Esfera>(['federal', 'estadual', 'municipal'])

export function pageRequestFromSearch(
  sp: Record<string, string | string[] | undefined>,
): PageRequest {
  const esferaRaw = first(sp.esfera)
  const esfera = esferaRaw && ESFERAS.has(esferaRaw as Esfera) ? (esferaRaw as Esfera) : undefined
  const anoRaw = first(sp.ano)
  const ano = anoRaw ? Number.parseInt(anoRaw, 10) : undefined

  return {
    skip: intOr(first(sp.skip), 0, 0, 1_000_000),
    take: intOr(first(sp.take), DEFAULT_TAKE, 1, MAX_TAKE),
    q: first(sp.q)?.trim() || undefined,
    uf: first(sp.uf)?.trim().toUpperCase() || undefined,
    municipioIbge: first(sp.municipioIbge)?.trim() || undefined,
    esfera,
    orgaoId: first(sp.orgaoId) || undefined,
    fornecedorId: first(sp.fornecedorId) || undefined,
    contratacaoId: first(sp.contratacaoId) || undefined,
    ano: ano && Number.isFinite(ano) ? ano : undefined,
    quarter: first(sp.quarter) || undefined,
  }
}

export function toQuery(req: Partial<PageRequest> & Record<string, string | number | undefined>): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(req)) {
    if (value == null || value === '') continue
    params.set(key, String(value))
  }
  const s = params.toString()
  return s ? `?${s}` : ''
}

export function rangeLabel(skip: number, take: number, total: number): string {
  if (total === 0) return '0 de 0'
  const from = skip + 1
  const to = Math.min(skip + take, total)
  return `${from}-${to} de ${total}`
}
