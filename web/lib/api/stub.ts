import { coverageFromItems } from '@/lib/coverage'
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
  Totals,
} from '@/lib/types'
import { ApiNotFoundError } from '@/lib/types'
import { contratacoes, fornecedores, items, orgaos } from '@/lib/api/fixtures'

function norm(s: string): string {
  return s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
}

function matchesQ(q: string | undefined, parts: Array<string | null | undefined>): boolean {
  if (!q) return true
  const n = norm(q)
  return parts.some((p) => p != null && norm(p).includes(n))
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
  const ctIds = new Set(contratacoes.filter((c) => c.orgaoId === orgaoId).map((c) => c.id))
  return items.filter((i) => ctIds.has(i.contratacaoId))
}

function totalsFor(itemRows: Item[], cts: Contratacao[]): Totals {
  const valores = cts.map((c) => c.valorHomologado).filter((v): v is number => v != null)
  return {
    contratacoes: cts.length,
    items: itemRows.length,
    valorHomologado: valores.length ? valores.reduce((a, b) => a + b, 0) : null,
    coverage: coverageFromItems(itemRows),
  }
}

function requireOrgao(id: string): Orgao {
  const row = orgaos.find((o) => o.id === id)
  if (!row) throw new ApiNotFoundError('orgao', id)
  return row
}

function requireFornecedor(id: string): Fornecedor {
  const row = fornecedores.find((f) => f.id === id)
  if (!row) throw new ApiNotFoundError('fornecedor', id)
  return row
}

function requireContratacao(id: string): Contratacao {
  const row = contratacoes.find((c) => c.id === id)
  if (!row) throw new ApiNotFoundError('contratacao', id)
  return row
}

export const stubClient: ExplorerClient = {
  async listOrgaos(req) {
    const rows = orgaos
      .filter((o) => matchesQ(req.q, [o.razaoSocial, o.cnpj, o.municipioNome, o.uf]))
      .filter((o) => !req.uf || o.uf === req.uf)
      .filter((o) => !req.esfera || o.esfera === req.esfera)
      .slice()
      .sort((a, b) => a.razaoSocial.localeCompare(b.razaoSocial, 'pt-BR'))
    const related = rows.flatMap((o) => orgaoItems(o.id))
    return page(rows, req, related)
  },

  async getOrgao(id) {
    const row = requireOrgao(id)
    const cts = contratacoes.filter((c) => c.orgaoId === id)
    const itemRows = orgaoItems(id)
    const detail: OrgaoDetail = {
      ...row,
      coverage: coverageFromItems(itemRows),
      totals: totalsFor(itemRows, cts),
    }
    return detail
  },

  async listFornecedores(req) {
    const rows = fornecedores
      .filter((f) => matchesQ(req.q, [f.razaoSocial, f.cnpj, f.cnae]))
      .slice()
      .sort((a, b) => a.razaoSocial.localeCompare(b.razaoSocial, 'pt-BR'))
    const related = items.filter((i) => rows.some((f) => f.id === i.fornecedorId))
    return page(rows, req, related)
  },

  async getFornecedor(id) {
    const row = requireFornecedor(id)
    const itemRows = items.filter((i) => i.fornecedorId === id)
    const ctIds = new Set(itemRows.map((i) => i.contratacaoId))
    const cts = contratacoes.filter((c) => ctIds.has(c.id))
    const detail: FornecedorDetail = {
      ...row,
      coverage: coverageFromItems(itemRows),
      totals: totalsFor(itemRows, cts),
    }
    return detail
  },

  async listContratacoes(req) {
    const rows = contratacoes
      .filter((c) => matchesQ(req.q, [c.objeto, c.pncpId, c.modalidade, c.source]))
      .filter((c) => !req.orgaoId || c.orgaoId === req.orgaoId)
      .filter((c) => {
        if (!req.fornecedorId) return true
        return items.some((i) => i.contratacaoId === c.id && i.fornecedorId === req.fornecedorId)
      })
      .filter((c) => !req.ano || c.ano === req.ano)
      .slice()
      .sort((a, b) => (b.publicadoEm ?? '').localeCompare(a.publicadoEm ?? ''))
    const related = items.filter((i) => rows.some((c) => c.id === i.contratacaoId))
    return page(rows, req, related)
  },

  async getContratacao(id) {
    const row = requireContratacao(id)
    const itemRows = items.filter((i) => i.contratacaoId === id)
    const detail: ContratacaoDetail = {
      ...row,
      orgao: requireOrgao(row.orgaoId),
      coverage: coverageFromItems(itemRows),
      itemCount: itemRows.length,
    }
    return detail
  },

  async listItems(req) {
    const rows = items
      .filter((i) =>
        matchesQ(req.q, [i.descricao, i.catmat, i.catser, i.unidadeMedida, i.snapshotId]),
      )
      .filter((i) => !req.contratacaoId || i.contratacaoId === req.contratacaoId)
      .filter((i) => !req.fornecedorId || i.fornecedorId === req.fornecedorId)
      .filter((i) => !req.uf || i.uf === req.uf)
      .filter((i) => !req.quarter || i.quarter === req.quarter)
      .filter((i) => {
        if (!req.orgaoId) return true
        const ct = contratacoes.find((c) => c.id === i.contratacaoId)
        return ct?.orgaoId === req.orgaoId
      })
      .slice()
      .sort((a, b) => a.descricao.localeCompare(b.descricao, 'pt-BR'))
    return page(rows, req, rows)
  },

  async getItem(id) {
    const row = items.find((i) => i.id === id)
    if (!row) throw new ApiNotFoundError('item', id)
    const ct = requireContratacao(row.contratacaoId)
    const peers = items.filter((i) => i.uf === row.uf && i.quarter === row.quarter)
    const detail: ItemDetail = {
      ...row,
      contratacao: ct,
      orgao: requireOrgao(ct.orgaoId),
      fornecedor: row.fornecedorId ? requireFornecedor(row.fornecedorId) : null,
      coverage: coverageFromItems(peers),
    }
    return detail
  },
}

export const stubSliceCoverage = coverageFromItems(items)
