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
  { nome: 'Santana', uf: 'AP', ibge: '1600600' },
  { nome: 'Rorainópolis', uf: 'RR', ibge: '1400472' },
  { nome: 'Maringá', uf: 'PR', ibge: '4115200' },
  { nome: 'Taubaté', uf: 'SP', ibge: '3554102' },
  { nome: 'Cascavel', uf: 'PR', ibge: '4104808' },
  { nome: 'Juiz de Fora', uf: 'MG', ibge: '3136702' },
  { nome: 'Foz do Iguaçu', uf: 'PR', ibge: '4108304' },
  { nome: 'Santa Maria', uf: 'RS', ibge: '4316907' },
  { nome: 'Montes Claros', uf: 'MG', ibge: '3143302' },
  { nome: 'Governador Valadares', uf: 'MG', ibge: '3127701' },
  { nome: 'Canoas', uf: 'RS', ibge: '4304606' },
  { nome: 'Lages', uf: 'SC', ibge: '4209300' },
  { nome: 'Santarém', uf: 'PA', ibge: '1506807' },
  { nome: 'Rio Verde', uf: 'GO', ibge: '5218805' },
  { nome: 'Paulo Afonso', uf: 'BA', ibge: '2924009' },
  { nome: 'São Lourenço da Mata', uf: 'PE', ibge: '2613701' },
  { nome: 'Crato', uf: 'CE', ibge: '2304202' },
  { nome: 'Ariquemes', uf: 'RO', ibge: '1100023' },
  { nome: 'Colatina', uf: 'ES', ibge: '3201506' },
  { nome: 'Castanhal', uf: 'PA', ibge: '1502400' },
  { nome: 'Divinópolis', uf: 'MG', ibge: '3122306' },
  { nome: 'Petrópolis', uf: 'RJ', ibge: '3303906' },
  { nome: 'Ipatinga', uf: 'MG', ibge: '3131307' },
  { nome: 'Macaé', uf: 'RJ', ibge: '3302403' },
] as const

export const SLICE_BRAND = 'Quarenta e cinco municípios · 2024'

export const SLICE_LABEL =
  'Volta Redonda e Niterói (RJ), Bauru (SP), Caxias do Sul (RS), Joinville (SC), Uberlândia (MG), Londrina (PR), Feira de Santana (BA), Caruaru (PE), Anápolis (GO), Vila Velha (ES), Campina Grande (PB), Caucaia (CE), Imperatriz (MA), Arapiraca (AL), Dourados (MS), Marabá (PA), Várzea Grande (MT), Ji-Paraná (RO), Parnamirim (RN), Cruzeiro do Sul (AC), Santana (AP), Rorainópolis (RR), Maringá (PR), Taubaté (SP), Cascavel (PR), Juiz de Fora (MG), Foz do Iguaçu (PR), Santa Maria (RS), Montes Claros (MG), Governador Valadares (MG), Canoas (RS), Lages (SC), Santarém (PA), Rio Verde (GO), Paulo Afonso (BA), São Lourenço da Mata (PE), Crato (CE), Ariquemes (RO), Colatina (ES), Castanhal (PA), Divinópolis (MG), Petrópolis (RJ), Ipatinga (MG) e Macaé (RJ) · 2024'

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
