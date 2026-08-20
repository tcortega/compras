import { readCoverage } from '@/lib/coverage'
import type {
  Contratacao,
  ContratacaoDetail,
  ExplorerClient,
  Fornecedor,
  FornecedorDetail,
  Item,
  ItemDetail,
  Orgao,
  OrgaoDetail,
  PageRequest,
  SkipTakePage,
} from '@/lib/types'
import { ApiError, ApiNotFoundError } from '@/lib/types'

const ENTITY_REVALIDATE = 3600

function queryOf(req: PageRequest): string {
  const params = new URLSearchParams()
  params.set('skip', String(req.skip))
  params.set('take', String(req.take))
  if (req.q) params.set('q', req.q)
  if (req.uf) params.set('uf', req.uf)
  if (req.esfera) params.set('esfera', req.esfera)
  if (req.orgaoId) params.set('orgaoId', req.orgaoId)
  if (req.fornecedorId) params.set('fornecedorId', req.fornecedorId)
  if (req.contratacaoId) params.set('contratacaoId', req.contratacaoId)
  if (req.ano != null) params.set('ano', String(req.ano))
  if (req.quarter) params.set('quarter', req.quarter)
  return params.toString()
}

function asPage<T>(raw: unknown, skip: number, take: number): SkipTakePage<T> {
  const o = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {}
  const items = Array.isArray(o.items) ? (o.items as T[]) : []
  const total = typeof o.total === 'number' ? o.total : items.length
  return {
    items,
    total,
    skip: typeof o.skip === 'number' ? o.skip : skip,
    take: typeof o.take === 'number' ? o.take : take,
    coverage: readCoverage(o.coverage),
  }
}

export function createHttpClient(baseUrl: string): ExplorerClient {
  const root = baseUrl.replace(/\/$/, '')

  async function getJson<T>(path: string, revalidate = ENTITY_REVALIDATE): Promise<T> {
    const url = `${root}${path}`
    const res = await fetch(url, {
      headers: { accept: 'application/json' },
      next: { revalidate },
    })
    if (res.status === 404) {
      const m = /\/api\/([^/]+)\/([^/?#]+)/.exec(path)
      throw new ApiNotFoundError(m?.[1] ?? 'recurso', m?.[2] ?? '')
    }
    if (!res.ok) {
      throw new ApiError(res.status, `API ${res.status} em ${path}`)
    }
    return (await res.json()) as T
  }

  return {
    async listOrgaos(req) {
      const raw = await getJson<unknown>(`/api/orgaos?${queryOf(req)}`, 60)
      return asPage<Orgao>(raw, req.skip, req.take)
    },
    async getOrgao(id) {
      return getJson<OrgaoDetail>(`/api/orgaos/${id}`)
    },
    async listFornecedores(req) {
      const raw = await getJson<unknown>(`/api/fornecedores?${queryOf(req)}`, 60)
      return asPage<Fornecedor>(raw, req.skip, req.take)
    },
    async getFornecedor(id) {
      return getJson<FornecedorDetail>(`/api/fornecedores/${id}`)
    },
    async listContratacoes(req) {
      const raw = await getJson<unknown>(`/api/contratacoes?${queryOf(req)}`, 60)
      return asPage<Contratacao>(raw, req.skip, req.take)
    },
    async getContratacao(id) {
      return getJson<ContratacaoDetail>(`/api/contratacoes/${id}`)
    },
    async listItems(req) {
      const raw = await getJson<unknown>(`/api/items?${queryOf(req)}`, 60)
      return asPage<Item>(raw, req.skip, req.take)
    },
    async getItem(id) {
      return getJson<ItemDetail>(`/api/items/${id}`)
    },
  }
}
