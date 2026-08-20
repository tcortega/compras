import { cache } from 'react'
import { createHttpClient } from '@/lib/api/http'
import { stubClient } from '@/lib/api/stub'
import { SLICE_YEAR, SLICE_YEAR_CANDIDATES } from '@/lib/copy'
import { fillCoverage, overlaySlice } from '@/lib/coverage'
import type { CoberturaPayload, Coverage, ExplorerClient, SkipTakePage } from '@/lib/types'

export { ids } from '@/lib/api/fixtures'

function resolveBase(): string {
  return (process.env.API_BASE_URL ?? 'stub').trim()
}

export function usesStubApi(): boolean {
  const base = resolveBase()
  return base === '' || base === 'stub'
}

export function getClient(): ExplorerClient {
  if (usesStubApi()) return stubClient
  return createHttpClient(resolveBase())
}

export const loadSliceCoverage = cache(async (): Promise<Coverage> => {
  const page = await getClient().listItems({ skip: 0, take: 100 })
  return fillCoverage(page.coverage, page.items)
})

export const loadCobertura = cache(async (): Promise<CoberturaPayload> => getClient().getCobertura())

export const loadSliceYears = cache(async (): Promise<number[]> => {
  try {
    const payload = await loadCobertura()
    if (payload.years.length) return payload.years
  } catch {
    // fall through to contratacao probes
  }
  try {
    const found: number[] = []
    for (const ano of SLICE_YEAR_CANDIDATES) {
      const page = await getClient().listContratacoes({ skip: 0, take: 1, ano })
      if (page.total > 0) found.push(ano)
    }
    return found.length ? found : [SLICE_YEAR]
  } catch {
    return [SLICE_YEAR]
  }
})

async function withSlice<T>(page: SkipTakePage<T>): Promise<SkipTakePage<T>> {
  const slice = await loadSliceCoverage()
  return { ...page, coverage: overlaySlice(page.coverage, slice) }
}

export const api: ExplorerClient = {
  listOrgaos: (req) => getClient().listOrgaos(req).then(withSlice),
  getOrgao: (id) => getClient().getOrgao(id),
  listFornecedores: (req) => getClient().listFornecedores(req).then(withSlice),
  getFornecedor: (id) => getClient().getFornecedor(id),
  listContratacoes: (req) => getClient().listContratacoes(req).then(withSlice),
  getContratacao: (id) => getClient().getContratacao(id),
  listItems: (req) => getClient().listItems(req).then(withSlice),
  getItem: (id) => getClient().getItem(id),
  getCobertura: () => getClient().getCobertura(),
}

export async function safeDetail<T>(load: () => Promise<T>): Promise<T | null> {
  try {
    return await load()
  } catch (err) {
    if (err && typeof err === 'object' && 'status' in err && (err as { status: number }).status === 404) {
      return null
    }
    throw err
  }
}
