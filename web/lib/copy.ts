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
  { nome: 'Feira de Santana', uf: 'BA', ibge: '2910800' },
  { nome: 'Caruaru', uf: 'PE', ibge: '2604106' },
  { nome: 'Anápolis', uf: 'GO', ibge: '5201108' },
  { nome: 'Vila Velha', uf: 'ES', ibge: '3205200' },
  { nome: 'Campina Grande', uf: 'PB', ibge: '2504009' },
  { nome: 'Caucaia', uf: 'CE', ibge: '2303709' },
  { nome: 'Imperatriz', uf: 'MA', ibge: '2105302' },
  { nome: 'Arapiraca', uf: 'AL', ibge: '2700300' },
  { nome: 'Dourados', uf: 'MS', ibge: '5003702' },
  { nome: 'Marabá', uf: 'PA', ibge: '1504208' },
  { nome: 'Várzea Grande', uf: 'MT', ibge: '5108402' },
  { nome: 'Ji-Paraná', uf: 'RO', ibge: '1100122' },
  { nome: 'Parnamirim', uf: 'RN', ibge: '2403251' },
  { nome: 'Cruzeiro do Sul', uf: 'AC', ibge: '1200203' },
] as const

export const SLICE_BRAND = 'Vinte e um municípios · 2024'

export const SLICE_LABEL =
  'Volta Redonda e Niterói (RJ), Bauru (SP), Caxias do Sul (RS), Joinville (SC), Uberlândia (MG), Londrina (PR), Feira de Santana (BA), Caruaru (PE), Anápolis (GO), Vila Velha (ES), Campina Grande (PB), Caucaia (CE), Imperatriz (MA), Arapiraca (AL), Dourados (MS), Marabá (PA), Várzea Grande (MT), Ji-Paraná (RO), Parnamirim (RN) e Cruzeiro do Sul (AC) · 2024'

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
