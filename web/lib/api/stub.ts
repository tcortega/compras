import { coverageFromItems } from '@/lib/coverage'
import type {
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
  return {
    items: rows.slice(skip, skip + take),
    total: rows.length,
    skip,
    take,
    coverage: coverageFromItems(coverageItems),
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
}
