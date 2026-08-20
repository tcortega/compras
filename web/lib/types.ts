export type Esfera = 'federal' | 'estadual' | 'municipal'

export type Coverage = {
  n: number
  uf: string | null
  quarter: string | null
  methodologyVersion: string
}

export type PageRequest = {
  skip: number
  take: number
  q?: string
  uf?: string
  municipioIbge?: string
  esfera?: Esfera
  orgaoId?: string
  fornecedorId?: string
  contratacaoId?: string
  ano?: number
  quarter?: string
}

export type SkipTakePage<T> = {
  items: T[]
  total: number
  skip: number
  take: number
  coverage: Coverage
}

export type Orgao = {
  id: string
  cnpj: string
  razaoSocial: string
  esfera: Esfera
  poder: string
  uf: string
  municipioIbge: string
  municipioNome: string
  suspended: boolean
  createdAt: string
  updatedAt: string
}

export type FornecedorSocio = {
  nome: string
  cpfMasked: string | null
  qualificacao: string | null
}

export type Fornecedor = {
  id: string
  cnpj: string
  razaoSocial: string
  openedOn: string | null
  cnae: string | null
  cnaeDescricao?: string | null
  idadeCadastral?: string | null
  idadeAsOf?: string | null
  qsa?: FornecedorSocio[]
  suspended: boolean
  createdAt: string
  updatedAt: string
}

export type Contratacao = {
  id: string
  pncpId: string
  orgaoId: string
  modalidade: string
  objeto: string
  ano: number
  valorHomologado: number | null
  publicadoEm: string | null
  source: string
  snapshotId: string
  methodologyVersion: string
  suspended: boolean
  createdAt: string
  updatedAt: string
}

export type Item = {
  id: string
  contratacaoId: string
  fornecedorId: string | null
  descricao: string
  catmat: string | null
  catser: string | null
  quantidade: number
  unidadeMedida: string
  unidadeCanonica: string | null
  valorUnitario: number | null
  valorTotal: number | null
  valorPorUnidadeCanonica?: number | null
  uf: string
  quarter: string
  snapshotId: string
  methodologyVersion: string
  suspended: boolean
  createdAt: string
  updatedAt: string
}

export type CoberturaMunicipio = {
  nome: string
  uf: string
  ibge: string
}

export type CoberturaYearCount = {
  year: number
  compras: number
  items: number
}

export type CoberturaSource = {
  name: string
  lastUpdate: string | null
  n: number
}

export type CoberturaPayload = {
  municipios: { n: number; items: CoberturaMunicipio[] }
  years: number[]
  rows: { compras: number; items: number; perYear: CoberturaYearCount[] }
  catmatCoveragePercent: number
  nCoded: number
  nItems: number
  sources: CoberturaSource[]
  coverage: Coverage
}

export type SearchSource = 'meilisearch' | 'unset' | 'unavailable' | 'warehouse'

export type SearchPage = {
  orgaos: SkipTakePage<Orgao>
  fornecedores: SkipTakePage<Fornecedor>
  items: SkipTakePage<Item>
  coverage: Coverage
  source: SearchSource
}

export type ExplorerClient = {
  listOrgaos: (req: PageRequest) => Promise<SkipTakePage<Orgao>>
  getOrgao: (id: string) => Promise<Orgao>
  listFornecedores: (req: PageRequest) => Promise<SkipTakePage<Fornecedor>>
  getFornecedor: (id: string) => Promise<Fornecedor>
  listContratacoes: (req: PageRequest) => Promise<SkipTakePage<Contratacao>>
  getContratacao: (id: string) => Promise<Contratacao>
  listItems: (req: PageRequest) => Promise<SkipTakePage<Item>>
  getItem: (id: string) => Promise<Item>
  getCobertura: () => Promise<CoberturaPayload>
  search: (req: PageRequest) => Promise<SearchPage>
}

export function isPublished<T extends { suspended?: boolean }>(row: T): boolean {
  return row.suspended !== true
}

export class ApiNotFoundError extends Error {
  readonly status = 404
  constructor(resource: string, id: string) {
    super(`${resource} ${id} não encontrado`)
    this.name = 'ApiNotFoundError'
  }
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}
