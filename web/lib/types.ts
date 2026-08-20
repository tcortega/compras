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
  createdAt: string
  updatedAt: string
}

export type Fornecedor = {
  id: string
  cnpj: string
  razaoSocial: string
  openedOn: string | null
  cnae: string | null
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
  uf: string
  quarter: string
  snapshotId: string
  methodologyVersion: string
  createdAt: string
  updatedAt: string
}

export type Totals = {
  contratacoes: number
  items: number
  valorHomologado: number | null
  coverage: Coverage
}

export type OrgaoDetail = Orgao & {
  coverage: Coverage
  totals: Totals
}

export type FornecedorDetail = Fornecedor & {
  coverage: Coverage
  totals: Totals
}

export type ContratacaoDetail = Contratacao & {
  orgao: Orgao
  coverage: Coverage
  itemCount: number
}

export type ItemDetail = Item & {
  contratacao: Contratacao
  orgao: Orgao
  fornecedor: Fornecedor | null
  coverage: Coverage
}

export type ExplorerClient = {
  listOrgaos: (req: PageRequest) => Promise<SkipTakePage<Orgao>>
  getOrgao: (id: string) => Promise<OrgaoDetail>
  listFornecedores: (req: PageRequest) => Promise<SkipTakePage<Fornecedor>>
  getFornecedor: (id: string) => Promise<FornecedorDetail>
  listContratacoes: (req: PageRequest) => Promise<SkipTakePage<Contratacao>>
  getContratacao: (id: string) => Promise<ContratacaoDetail>
  listItems: (req: PageRequest) => Promise<SkipTakePage<Item>>
  getItem: (id: string) => Promise<ItemDetail>
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
