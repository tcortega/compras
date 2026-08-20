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
  const ufs = [...new Set(items.map((i) => i.uf))]
  const quarters = [...new Set(items.map((i) => i.quarter))]
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

export function fillCoverage(coverage: Coverage, rows: readonly unknown[]): Coverage {
  if (coverage.uf) return coverage
  const ufs = [
    ...new Set(
      rows.flatMap((row) => {
        if (!row || typeof row !== 'object' || !('uf' in row)) return []
        const uf = (row as { uf?: unknown }).uf
        return typeof uf === 'string' && uf ? [uf] : []
      }),
    ),
  ]
  return { ...coverage, uf: ufs.length === 1 ? (ufs[0] ?? null) : coverage.uf }
}

export function coverageParts(c: Coverage): { n: string; geo: string; when: string; method: string } {
  return {
    n: `n=${c.n}`,
    geo: c.n === 0 ? 'filtro sem registros' : c.uf ? `UF ${c.uf}` : 'UF mista',
    when: c.n === 0 ? 'neste recorte' : c.quarter ? formatQuarter(c.quarter) : 'vários trimestres',
    method: `metodologia ${c.methodologyVersion}`,
  }
}

export function coverageText(c: Coverage): string {
  const p = coverageParts(c)
  return `${p.n} · ${p.geo} · ${p.when} · ${p.method}`
}
