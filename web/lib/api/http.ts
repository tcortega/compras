import { fillCoverage, readCoverage } from '@/lib/coverage'
import type {
  CoberturaPayload,
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

const STUB_MARKERS = [
  '7c2e1f40-3306-4050',
  '8d3f2a51-3306-4050',
  '9e4a3b62-3306-4050',
  'ae5b4c73-3306-4050',
  'sha256:dev-slice-vr-2024',
]

function assertNotStubPayload(payload: unknown, path: string): void {
  const blob = JSON.stringify(payload)
  const hit = STUB_MARKERS.find((marker) => blob.includes(marker))
  if (hit) {
    throw new ApiError(502, `API devolveu recorte stub em ${path}`)
  }
}

function queryOf(req: PageRequest): string {
  const params = new URLSearchParams()
  params.set('skip', String(req.skip))
  params.set('take', String(req.take))
  if (req.q) params.set('q', req.q)
  if (req.uf) params.set('uf', req.uf)
  if (req.municipioIbge) params.set('municipioIbge', req.municipioIbge)
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
  const coverage = fillCoverage(readCoverage(o.coverage), items)
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
    const payload = (await res.json()) as T
    assertNotStubPayload(payload, path)
    return payload
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
    async getCobertura() {
      return readCobertura(await getJson<unknown>('/api/cobertura', 60))
    },
  }
}

function readCobertura(raw: unknown): CoberturaPayload {
  if (!raw || typeof raw !== 'object') {
    throw new ApiError(502, 'API sem cobertura em /api/cobertura')
  }
  const o = raw as Record<string, unknown>
  const municipiosRaw = o.municipios && typeof o.municipios === 'object' ? (o.municipios as Record<string, unknown>) : {}
  const rowsRaw = o.rows && typeof o.rows === 'object' ? (o.rows as Record<string, unknown>) : {}
  const municipios = Array.isArray(municipiosRaw.items) ? municipiosRaw.items : []
  const perYear = Array.isArray(rowsRaw.perYear) ? rowsRaw.perYear : []
  const sources = Array.isArray(o.sources) ? o.sources : []
  const years = Array.isArray(o.years) ? o.years.filter((y): y is number => typeof y === 'number') : []
  return {
    municipios: {
      n: typeof municipiosRaw.n === 'number' ? municipiosRaw.n : municipios.length,
      items: municipios as CoberturaPayload['municipios']['items'],
    },
    years,
    rows: {
      compras: typeof rowsRaw.compras === 'number' ? rowsRaw.compras : 0,
      items: typeof rowsRaw.items === 'number' ? rowsRaw.items : 0,
      perYear: perYear as CoberturaPayload['rows']['perYear'],
    },
    catmatCoveragePercent: typeof o.catmatCoveragePercent === 'number' ? o.catmatCoveragePercent : 0,
    nCoded: typeof o.nCoded === 'number' ? o.nCoded : 0,
    nItems: typeof o.nItems === 'number' ? o.nItems : 0,
    sources: sources as CoberturaPayload['sources'],
    coverage: readCoverage(o.coverage),
  }
}
