import { readCoverage } from '@/lib/coverage'
import type {
  Contratacao,
  ExplorerClient,
  Fornecedor,
  Item,
  Orgao,
  PageRequest,
  SkipTakePage,
} from '@/lib/types'
import { ApiError, ApiNotFoundError, isPublished } from '@/lib/types'

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

function publishedPage<T extends { suspended?: boolean }>(
  raw: unknown,
  skip: number,
  take: number,
): SkipTakePage<T> {
  const o = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {}
  const items = (Array.isArray(o.items) ? (o.items as T[]) : []).filter(isPublished)
  const coverage = readCoverage(o.coverage)
  const total = typeof o.total === 'number' ? o.total : coverage.n
  return {
    items,
    total,
    skip: typeof o.skip === 'number' ? o.skip : skip,
    take: typeof o.take === 'number' ? o.take : take,
    coverage,
  }
}

function readPublishedEntity<T extends { suspended?: boolean }>(
  raw: unknown,
  resource: string,
  id: string,
  wrapperKey?: 'contratacao' | 'item',
): T {
  if (!raw || typeof raw !== 'object') {
    throw new ApiError(502, `API sem entidade em /api/${resource}/${id}`)
  }
  const o = raw as Record<string, unknown>
  const wrapped = wrapperKey ? o[wrapperKey] : undefined
  const row = (wrapped && typeof wrapped === 'object' && !Array.isArray(wrapped) ? wrapped : raw) as T
  if (!isPublished(row)) throw new ApiNotFoundError(resource, id)
  return row
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
      return publishedPage<Orgao>(raw, req.skip, req.take)
    },
    async getOrgao(id) {
      return readPublishedEntity<Orgao>(await getJson<unknown>(`/api/orgaos/${id}`), 'orgao', id)
    },
    async listFornecedores(req) {
      const raw = await getJson<unknown>(`/api/fornecedores?${queryOf(req)}`, 60)
      return publishedPage<Fornecedor>(raw, req.skip, req.take)
    },
    async getFornecedor(id) {
      return readPublishedEntity<Fornecedor>(
        await getJson<unknown>(`/api/fornecedores/${id}`),
        'fornecedor',
        id,
      )
    },
    async listContratacoes(req) {
      const raw = await getJson<unknown>(`/api/contratacoes?${queryOf(req)}`, 60)
      return publishedPage<Contratacao>(raw, req.skip, req.take)
    },
    async getContratacao(id) {
      return readPublishedEntity<Contratacao>(
        await getJson<unknown>(`/api/contratacoes/${id}`),
        'contratacao',
        id,
        'contratacao',
      )
    },
    async listItems(req) {
      const raw = await getJson<unknown>(`/api/items?${queryOf(req)}`, 60)
      return publishedPage<Item>(raw, req.skip, req.take)
    },
    async getItem(id) {
      return readPublishedEntity<Item>(await getJson<unknown>(`/api/items/${id}`), 'item', id, 'item')
    },
  }
}
