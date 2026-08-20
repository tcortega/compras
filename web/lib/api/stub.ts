import { coverageFromItems } from '@/lib/coverage'
import type {
  CoberturaMunicipio,
  CoberturaPayload,
  Contratacao,
  ExplorerClient,
  Fornecedor,
  Item,
  Orgao,
  PageRequest,
  SkipTakePage,
} from '@/lib/types'
import { ApiNotFoundError, isPublished } from '@/lib/types'
import { contratacoes, fornecedores, items, orgaos } from '@/lib/api/fixtures'

function norm(s: string): string {
  return s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
}

function matchesQ(q: string | undefined, parts: Array<string | null | undefined>): boolean {
  if (!q) return true
  const n = norm(q)
  return parts.some((p) => p != null && norm(p).includes(n))
}

function liveOrgaos(): Orgao[] {
  return orgaos.filter(isPublished)
}

function liveFornecedores(): Fornecedor[] {
  return fornecedores.filter(isPublished)
}

function liveContratacoes(): Contratacao[] {
  const hiddenOrgaos = new Set(orgaos.filter((o) => !isPublished(o)).map((o) => o.id))
  return contratacoes.filter((c) => isPublished(c) && !hiddenOrgaos.has(c.orgaoId))
}

function liveItems(): Item[] {
  const liveCtIds = new Set(liveContratacoes().map((c) => c.id))
  const hiddenFornecedores = new Set(fornecedores.filter((f) => !isPublished(f)).map((f) => f.id))
  return items.filter((i) => {
    if (!isPublished(i)) return false
    if (!liveCtIds.has(i.contratacaoId)) return false
    if (i.fornecedorId && hiddenFornecedores.has(i.fornecedorId)) return false
    return true
  })
}

function page<T>(rows: T[], req: PageRequest, coverageItems: Item[]): SkipTakePage<T> {
  const skip = req.skip
  const take = req.take
  const coverage = { ...coverageFromItems(coverageItems), n: rows.length }
  if (!coverage.uf) coverage.uf = req.uf ?? coverage.uf
  if (!coverage.quarter) coverage.quarter = req.quarter ?? coverage.quarter
  return {
    items: rows.slice(skip, skip + take),
    total: rows.length,
    skip,
    take,
    coverage,
  }
}

function orgaoItems(orgaoId: string): Item[] {
  const ctIds = new Set(liveContratacoes().filter((c) => c.orgaoId === orgaoId).map((c) => c.id))
  return liveItems().filter((i) => ctIds.has(i.contratacaoId))
}

function requireOrgao(id: string): Orgao {
  const row = liveOrgaos().find((o) => o.id === id)
  if (!row) throw new ApiNotFoundError('orgao', id)
  return row
}

function requireFornecedor(id: string): Fornecedor {
  const row = liveFornecedores().find((f) => f.id === id)
  if (!row) throw new ApiNotFoundError('fornecedor', id)
  return row
}

function requireContratacao(id: string): Contratacao {
  const row = liveContratacoes().find((c) => c.id === id)
  if (!row) throw new ApiNotFoundError('contratacao', id)
  return row
}

export const stubClient: ExplorerClient = {
  async listOrgaos(req) {
    const rows = liveOrgaos()
      .filter((o) => matchesQ(req.q, [o.razaoSocial, o.cnpj, o.municipioNome, o.uf]))
      .filter((o) => !req.uf || o.uf === req.uf)
      .filter((o) => !req.municipioIbge || o.municipioIbge === req.municipioIbge)
      .filter((o) => !req.esfera || o.esfera === req.esfera)
      .slice()
      .sort((a, b) => a.razaoSocial.localeCompare(b.razaoSocial, 'pt-BR'))
    const related = rows.flatMap((o) => orgaoItems(o.id))
    return page(rows, req, related)
  },

  async getOrgao(id) {
    return requireOrgao(id)
  },

  async listFornecedores(req) {
    const rows = liveFornecedores()
      .filter((f) => matchesQ(req.q, [f.razaoSocial, f.cnpj, f.cnae]))
      .slice()
      .sort((a, b) => a.razaoSocial.localeCompare(b.razaoSocial, 'pt-BR'))
    const related = liveItems().filter((i) => rows.some((f) => f.id === i.fornecedorId))
    return page(rows, req, related)
  },

  async getFornecedor(id) {
    return requireFornecedor(id)
  },

  async listContratacoes(req) {
    const publishedItems = liveItems()
    const rows = liveContratacoes()
      .filter((c) => matchesQ(req.q, [c.objeto, c.pncpId, c.modalidade, c.source]))
      .filter((c) => !req.orgaoId || c.orgaoId === req.orgaoId)
      .filter((c) => {
        if (!req.fornecedorId) return true
        return publishedItems.some((i) => i.contratacaoId === c.id && i.fornecedorId === req.fornecedorId)
      })
      .filter((c) => !req.ano || c.ano === req.ano)
      .slice()
      .sort((a, b) => (b.publicadoEm ?? '').localeCompare(a.publicadoEm ?? ''))
    const related = publishedItems.filter((i) => rows.some((c) => c.id === i.contratacaoId))
    return page(rows, req, related)
  },

  async getContratacao(id) {
    return requireContratacao(id)
  },

  async listItems(req) {
    const rows = liveItems()
      .filter((i) =>
        matchesQ(req.q, [i.descricao, i.catmat, i.catser, i.unidadeMedida, i.snapshotId]),
      )
      .filter((i) => !req.contratacaoId || i.contratacaoId === req.contratacaoId)
      .filter((i) => !req.fornecedorId || i.fornecedorId === req.fornecedorId)
      .filter((i) => !req.uf || i.uf === req.uf)
      .filter((i) => !req.quarter || i.quarter === req.quarter)
      .filter((i) => {
        if (!req.orgaoId) return true
        const ct = liveContratacoes().find((c) => c.id === i.contratacaoId)
        return ct?.orgaoId === req.orgaoId
      })
      .slice()
      .sort((a, b) => a.descricao.localeCompare(b.descricao, 'pt-BR'))
    return page(rows, req, rows)
  },

  async getItem(id) {
    const row = liveItems().find((i) => i.id === id)
    if (!row) throw new ApiNotFoundError('item', id)
    return row
  },

  async getCobertura() {
    return stubCobertura()
  },
}

const CATALOG_CATMAT = new Set(['123456', '654321', '463210', '880111', '880222', '880333', '880444', '880555', '880666'])
const CATALOG_CATSER = new Set(['10001'])
const LANDING_NAMES = [
  'compras_gov',
  'receita_cnpj',
  'ocds',
  'pncp_consulta',
  'tce_sp',
  'tce_rs',
  'cgu_ceis_cnep',
] as const

function catalogInt(raw: string | null | undefined): string {
  if (!raw) return ''
  const text = raw.trim()
  if (!text || /^(nan|none|null|-)$/i.test(text)) return ''
  const n = Number(text.replace(',', '.'))
  if (!Number.isFinite(n) || n <= 0) return ''
  return String(Math.trunc(n))
}

function stubCobertura(): CoberturaPayload {
  const cts = liveContratacoes()
  const items = liveItems()
  const orgaoById = new Map(liveOrgaos().map((o) => [o.id, o]))
  const seen = new Map<string, CoberturaMunicipio>()
  for (const c of cts) {
    const orgao = orgaoById.get(c.orgaoId)
    if (!orgao) continue
    const key = `${orgao.municipioIbge}:${orgao.uf}:${orgao.municipioNome}`
    if (!seen.has(key)) {
      seen.set(key, { nome: orgao.municipioNome, uf: orgao.uf, ibge: orgao.municipioIbge })
    }
  }
  const municipios = [...seen.values()].sort((a, b) => a.nome.localeCompare(b.nome, 'en') || a.ibge.localeCompare(b.ibge, 'en'))
  const years = [...new Set(cts.map((c) => c.ano))].sort((a, b) => a - b)
  const nCoded = items.filter((i) => {
    const mat = catalogInt(i.catmat)
    const ser = catalogInt(i.catser)
    return (mat && CATALOG_CATMAT.has(mat)) || (ser && CATALOG_CATSER.has(ser))
  }).length
  const percent = items.length === 0 ? 0 : Math.round((10000 * nCoded) / items.length) / 100
  const lastCompra = cts.reduce<string | null>((acc, c) => {
    const stamp = c.publicadoEm ?? c.updatedAt
    if (!stamp) return acc
    if (!acc || stamp > acc) return stamp
    return acc
  }, null)
  return {
    municipios: { n: municipios.length, items: municipios },
    years,
    rows: {
      compras: cts.length,
      items: items.length,
      perYear: years.map((year) => ({
        year,
        compras: cts.filter((c) => c.ano === year).length,
        items: items.filter((i) => {
          const ct = cts.find((c) => c.id === i.contratacaoId)
          return ct?.ano === year
        }).length,
      })),
    },
    catmatCoveragePercent: percent,
    nCoded,
    nItems: items.length,
    sources: LANDING_NAMES.map((name) =>
      name === 'compras_gov' && cts.length > 0
        ? { name, lastUpdate: lastCompra, n: cts.length }
        : { name, lastUpdate: null, n: 0 },
    ),
    coverage: coverageFromItems(items),
  }
}
