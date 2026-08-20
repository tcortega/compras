export const SITE_NAME = 'Compras'
export const SITE_TAG = 'Explorador de compras públicas'
export const METHOD_VERSION = '0.1'
export const SLICE_YEAR = 2024
export const SLICE_UF = 'RJ'
export const SLICE_IBGE = '3306305'
export const SLICE_MUNICIPIO = 'Volta Redonda'
export const SNAPSHOT_ID = 'sha256:dev-slice-vr-2024'

export const SLICE_MUNICIPIOS = [
  { nome: 'Volta Redonda', uf: 'RJ', ibge: '3306305' },
  { nome: 'Niterói', uf: 'RJ', ibge: '3303302' },
  { nome: 'Bauru', uf: 'SP', ibge: '3506003' },
  { nome: 'Caxias do Sul', uf: 'RS', ibge: '4305108' },
  { nome: 'Joinville', uf: 'SC', ibge: '4209102' },
  { nome: 'Uberlândia', uf: 'MG', ibge: '3170206' },
  { nome: 'Londrina', uf: 'PR', ibge: '4113700' },
] as const

export const SLICE_LABEL =
  'Volta Redonda e Niterói (RJ), Bauru (SP), Caxias do Sul (RS), Joinville (SC), Uberlândia (MG) e Londrina (PR) · 2024'

export const copy = {
  coverageIncomplete:
    'Cobertura incompleta. Este recorte não representa o país.',
  coverageExempt:
    'Municípios com menos de 20 mil habitantes estão dispensados de publicar no PNCP até 31 de março de 2027.',
  coverageQuality:
    'O TCU (Acórdão 53/2025) registrou inconsistência em 86,4% dos registros do PNCP. Os números abaixo são o recorte ingerido, não um censo nacional.',
  noValue: 'n/d',
  sourceLine: 'Fonte e recorte',
  searchPlaceholder: 'Itens, órgãos, fornecedores, CNPJ ou CATMAT',
  searchSubmit: 'Buscar',
  empty: 'Nenhum registro neste recorte para o filtro atual.',
  loadError: 'Não foi possível ler este recorte.',
  notFound: 'Registro não encontrado neste recorte.',
  skipTake: 'Paginação por skip e take, no servidor.',
} as const
