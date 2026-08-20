import { createHttpClient } from '@/lib/api/http'
import { stubClient } from '@/lib/api/stub'
import type { Coverage, ExplorerClient } from '@/lib/types'

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

export const api: ExplorerClient = {
  listOrgaos: (req) => getClient().listOrgaos(req),
  getOrgao: (id) => getClient().getOrgao(id),
  listFornecedores: (req) => getClient().listFornecedores(req),
  getFornecedor: (id) => getClient().getFornecedor(id),
  listContratacoes: (req) => getClient().listContratacoes(req),
  getContratacao: (id) => getClient().getContratacao(id),
  listItems: (req) => getClient().listItems(req),
  getItem: (id) => getClient().getItem(id),
}

export async function loadSliceCoverage(): Promise<Coverage> {
  const page = await api.listItems({ skip: 0, take: 1 })
  return page.coverage
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
