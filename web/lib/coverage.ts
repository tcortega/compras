import { METHOD_VERSION } from '@/lib/copy'
import type { Coverage, Item } from '@/lib/types'
import { formatQuarter } from '@/lib/format'

export function emptyCoverage(): Coverage {
  return {
    n: 0,
    uf: null,
    quarter: null,
    methodologyVersion: METHOD_VERSION,
  }
}

export function coverageFromItems(items: Item[]): Coverage {
  if (items.length === 0) return emptyCoverage()
  const ufs = [...new Set(items.map((i) => i.uf).filter(Boolean))]
  const quarters = [...new Set(items.map((i) => i.quarter).filter(Boolean))]
  return {
    n: items.length,
    uf: ufs.length === 1 ? (ufs[0] ?? null) : null,
    quarter: quarters.length === 1 ? (quarters[0] ?? null) : null,
    methodologyVersion: items[0]?.methodologyVersion ?? METHOD_VERSION,
  }
}

export function readCoverage(raw: unknown): Coverage {
  if (!raw || typeof raw !== 'object') return emptyCoverage()
  const o = raw as Record<string, unknown>
  const n = typeof o.n === 'number' && Number.isFinite(o.n) ? o.n : 0
  return {
    n,
    uf: typeof o.uf === 'string' && o.uf ? o.uf : null,
    quarter: typeof o.quarter === 'string' && o.quarter ? o.quarter : null,
    methodologyVersion:
      typeof o.methodologyVersion === 'string' && o.methodologyVersion
        ? o.methodologyVersion
        : 'desconhecida',
  }
}

function readRowSlice(row: unknown): { uf?: string; quarter?: string } {
  if (!row || typeof row !== 'object') return {}
  const o = row as Record<string, unknown>
  const nested =
    o.coverage && typeof o.coverage === 'object' && !Array.isArray(o.coverage)
      ? (o.coverage as Record<string, unknown>)
      : null
  const uf =
    (typeof o.uf === 'string' && o.uf) ||
    (nested && typeof nested.uf === 'string' && nested.uf) ||
    undefined
  const quarter =
    (typeof o.quarter === 'string' && o.quarter) ||
    (nested && typeof nested.quarter === 'string' && nested.quarter) ||
    undefined
  return { uf: uf || undefined, quarter: quarter || undefined }
}

function unique(values: string[]): string | null {
  const u = [...new Set(values)]
  return u.length === 1 ? (u[0] ?? null) : null
}

export function fillCoverage(coverage: Coverage, rows: readonly unknown[]): Coverage {
  const complete = rows.length >= coverage.n
  if (!complete) return coverage
  const parsed = rows.map(readRowSlice)
  return {
    ...coverage,
    uf: coverage.uf ?? unique(parsed.flatMap((p) => (p.uf ? [p.uf] : []))),
    quarter: coverage.quarter ?? unique(parsed.flatMap((p) => (p.quarter ? [p.quarter] : []))),
  }
}

export function overlaySlice(page: Coverage, slice: Coverage): Coverage {
  return {
    n: page.n,
    uf: page.uf ?? slice.uf,
    quarter: page.quarter ?? slice.quarter,
    methodologyVersion:
      page.methodologyVersion && page.methodologyVersion !== 'desconhecida'
        ? page.methodologyVersion
        : slice.methodologyVersion,
  }
}

export function coverageParts(c: Coverage): { n: string; geo: string; when: string; method: string } {
  return {
    n: `n=${c.n}`,
    geo: c.uf ? `UF ${c.uf}` : c.n === 0 ? 'filtro sem registros' : 'UF mista',
    when: c.quarter ? formatQuarter(c.quarter) : 'vários trimestres',
    method: `metodologia ${c.methodologyVersion}`,
  }
}

export function coverageText(c: Coverage): string {
  const p = coverageParts(c)
  return `${p.n} · ${p.geo} · ${p.when} · ${p.method}`
}
