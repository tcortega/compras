export const SITE_NAME = 'Compras'
export const SITE_TAG = 'Explorador de compras públicas'
export const METHOD_VERSION = '0.2'
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
  { nome: 'Santa Luzia', uf: 'MG', ibge: '3157807' },
  { nome: 'Nova Friburgo', uf: 'RJ', ibge: '3303401' },
  { nome: 'Marília', uf: 'SP', ibge: '3529005' },
  { nome: 'Balneário Camboriú', uf: 'SC', ibge: '4202008' },
  { nome: 'Itaquaquecetuba', uf: 'SP', ibge: '3523107' },
  { nome: 'Praia Grande', uf: 'SP', ibge: '3541000' },
  { nome: 'São José dos Pinhais', uf: 'PR', ibge: '4125506' },
  { nome: 'Suzano', uf: 'SP', ibge: '3552502' },
  { nome: 'Guarujá', uf: 'SP', ibge: '3518701' },
  { nome: 'Cotia', uf: 'SP', ibge: '3513009' },
  { nome: 'Parauapebas', uf: 'PA', ibge: '1505536' },
  { nome: 'Jacareí', uf: 'SP', ibge: '3524402' },
  { nome: 'Itaboraí', uf: 'RJ', ibge: '3301900' },
  { nome: 'Maricá', uf: 'RJ', ibge: '3302700' },
  { nome: 'Brasiléia', uf: 'AC', ibge: '1200104' },
  { nome: 'Manoel Urbano', uf: 'AC', ibge: '1200344' },
  { nome: 'Rio Branco', uf: 'AC', ibge: '1200401' },
  { nome: 'Tarauacá', uf: 'AC', ibge: '1200609' },
  { nome: 'Capela', uf: 'AL', ibge: '2701704' },
  { nome: 'Dois Riachos', uf: 'AL', ibge: '2702504' },
  { nome: 'Rio Largo', uf: 'AL', ibge: '2707701' },
  { nome: 'União dos Palmares', uf: 'AL', ibge: '2709301' },
  { nome: 'Atalaia do Norte', uf: 'AM', ibge: '1300201' },
  { nome: 'Codajás', uf: 'AM', ibge: '1301308' },
  { nome: 'Silves', uf: 'AM', ibge: '1304005' },
  { nome: 'Macapá', uf: 'AP', ibge: '1600303' },
  { nome: 'Cocos', uf: 'BA', ibge: '2908101' },
  { nome: 'Ibirapitanga', uf: 'BA', ibge: '2912707' },
  { nome: 'Salinas da Margarida', uf: 'BA', ibge: '2927309' },
  { nome: 'Sapeaçu', uf: 'BA', ibge: '2929602' },
  { nome: 'Aquiraz', uf: 'CE', ibge: '2301000' },
  { nome: 'Fortaleza', uf: 'CE', ibge: '2304400' },
  { nome: 'Guaiúba', uf: 'CE', ibge: '2304954' },
  { nome: 'Horizonte', uf: 'CE', ibge: '2305233' },
  { nome: 'Jerônimo Monteiro', uf: 'ES', ibge: '3203106' },
  { nome: 'Muniz Freire', uf: 'ES', ibge: '3203700' },
  { nome: 'Presidente Kennedy', uf: 'ES', ibge: '3204302' },
  { nome: 'São Roque do Canaã', uf: 'ES', ibge: '3204955' },
  { nome: 'Cidade Ocidental', uf: 'GO', ibge: '5205497' },
  { nome: 'Goiandira', uf: 'GO', ibge: '5208509' },
  { nome: 'Itaberaí', uf: 'GO', ibge: '5210406' },
  { nome: 'Santo Antônio do Descoberto', uf: 'GO', ibge: '5219753' },
  { nome: 'Governador Edison Lobão', uf: 'MA', ibge: '2104552' },
  { nome: 'Santa Luzia do Paruá', uf: 'MA', ibge: '2110039' },
  { nome: 'São Domingos do Azeitão', uf: 'MA', ibge: '2110658' },
  { nome: 'São Luís', uf: 'MA', ibge: '2111300' },
  { nome: 'Belo Horizonte', uf: 'MG', ibge: '3106200' },
  { nome: 'Campo Belo', uf: 'MG', ibge: '3111200' },
  { nome: 'Cristais', uf: 'MG', ibge: '3120201' },
  { nome: 'Itabirito', uf: 'MG', ibge: '3131901' },
  { nome: 'Bataguassu', uf: 'MS', ibge: '5001904' },
  { nome: 'Maracaju', uf: 'MS', ibge: '5005400' },
  { nome: 'Cáceres', uf: 'MT', ibge: '5102504' },
  { nome: 'Santa Cruz do Xingu', uf: 'MT', ibge: '5107743' },
  { nome: 'Belterra', uf: 'PA', ibge: '1501451' },
  { nome: 'Salinópolis', uf: 'PA', ibge: '1506203' },
  { nome: 'São Domingos do Capim', uf: 'PA', ibge: '1507201' },
  { nome: 'Terra Santa', uf: 'PA', ibge: '1507979' },
  { nome: 'Alhandra', uf: 'PB', ibge: '2500601' },
  { nome: 'Cajazeiras', uf: 'PB', ibge: '2503704' },
  { nome: 'Monteiro', uf: 'PB', ibge: '2509701' },
  { nome: 'São Bento', uf: 'PB', ibge: '2513901' },
  { nome: 'Belo Jardim', uf: 'PE', ibge: '2601706' },
  { nome: 'Bezerros', uf: 'PE', ibge: '2601904' },
  { nome: 'Santa Terezinha', uf: 'PE', ibge: '2612802' },
  { nome: 'Terra Nova', uf: 'PE', ibge: '2615201' },
  { nome: 'Cajazeiras do Piauí', uf: 'PI', ibge: '2202075' },
  { nome: 'Francisco Santos', uf: 'PI', ibge: '2204204' },
  { nome: 'Sebastião Barros', uf: 'PI', ibge: '2210623' },
  { nome: 'Uruçuí', uf: 'PI', ibge: '2211209' },
  { nome: 'Cambé', uf: 'PR', ibge: '4103701' },
  { nome: 'Dois Vizinhos', uf: 'PR', ibge: '4107207' },
  { nome: 'Francisco Beltrão', uf: 'PR', ibge: '4108403' },
  { nome: 'Mariópolis', uf: 'PR', ibge: '4115309' },
  { nome: 'Pato Branco', uf: 'PR', ibge: '4118501' },
  { nome: 'Prudentópolis', uf: 'PR', ibge: '4120606' },
  { nome: 'Realeza', uf: 'PR', ibge: '4121406' },
  { nome: 'Salgado Filho', uf: 'PR', ibge: '4122800' },
  { nome: 'Telêmaco Borba', uf: 'PR', ibge: '4127106' },
  { nome: 'Turvo', uf: 'PR', ibge: '4127965' },
  { nome: 'Vera Cruz do Oeste', uf: 'PR', ibge: '4128559' },
  { nome: 'Angra dos Reis', uf: 'RJ', ibge: '3300100' },
  { nome: 'Itatiaia', uf: 'RJ', ibge: '3302254' },
  { nome: 'Rio de Janeiro', uf: 'RJ', ibge: '3304557' },
  { nome: 'São Pedro da Aldeia', uf: 'RJ', ibge: '3305208' },
  { nome: 'Caraúbas', uf: 'RN', ibge: '2402303' },
  { nome: 'Currais Novos', uf: 'RN', ibge: '2403103' },
  { nome: 'Natal', uf: 'RN', ibge: '2408102' },
  { nome: 'Buritis', uf: 'RO', ibge: '1100452' },
  { nome: 'Jaru', uf: 'RO', ibge: '1100114' },
  { nome: 'Porto Velho', uf: 'RO', ibge: '1100205' },
  { nome: 'Boa Vista', uf: 'RR', ibge: '1400100' },
  { nome: 'Cantá', uf: 'RR', ibge: '1400175' },
  { nome: 'Caracaraí', uf: 'RR', ibge: '1400209' },
  { nome: 'São Luiz', uf: 'RR', ibge: '1400605' },
  { nome: 'Cachoeirinha', uf: 'RS', ibge: '4303103' },
  { nome: 'Coronel Bicaco', uf: 'RS', ibge: '4305900' },
  { nome: 'São Luiz Gonzaga', uf: 'RS', ibge: '4318903' },
  { nome: 'São Vicente do Sul', uf: 'RS', ibge: '4319802' },
  { nome: 'Itá', uf: 'SC', ibge: '4208005' },
  { nome: 'Quilombo', uf: 'SC', ibge: '4214201' },
  { nome: 'Schroeder', uf: 'SC', ibge: '4217402' },
  { nome: 'Xanxerê', uf: 'SC', ibge: '4219507' },
  { nome: 'Botucatu', uf: 'SP', ibge: '3507506' },
  { nome: 'Buritama', uf: 'SP', ibge: '3508108' },
  { nome: 'Campinas', uf: 'SP', ibge: '3509502' },
  { nome: 'Guarulhos', uf: 'SP', ibge: '3518800' },
  { nome: 'Mogi Mirim', uf: 'SP', ibge: '3530805' },
  { nome: 'Pederneiras', uf: 'SP', ibge: '3536703' },
  { nome: 'Ribeirão Preto', uf: 'SP', ibge: '3543402' },
  { nome: 'Santa Rosa de Viterbo', uf: 'SP', ibge: '3547601' },
  { nome: 'São José da Bela Vista', uf: 'SP', ibge: '3549508' },
  { nome: 'Valinhos', uf: 'SP', ibge: '3556206' },
  { nome: 'Colinas do Tocantins', uf: 'TO', ibge: '1705508' },
] as const

export const SLICE_YEAR_CANDIDATES = [2024, 2025, 2026] as const

function formatSliceCities(rows: readonly { nome: string; uf: string }[]): string {
  const parts = rows.map((row) => `${row.nome} (${row.uf})`)
  const first = parts[0]
  if (first === undefined) return ''
  if (parts.length === 1) return first
  return `${parts.slice(0, -1).join(', ')} e ${parts[parts.length - 1] ?? first}`
}

export const SLICE_CITIES = formatSliceCities(SLICE_MUNICIPIOS)

export function sliceYearSpan(years: readonly number[]): string {
  const known = [...years].filter((year) => Number.isFinite(year)).sort((a, b) => a - b)
  const min = known[0]
  const max = known.at(-1)
  if (min === undefined || max === undefined) return String(SLICE_YEAR)
  if (min === max) return String(min)
  if (max >= 2026) return `${min}-${max} YTD`
  return `${min}-${max}`
}

function sliceMunicipioPhrase(n: number): string {
  if (n === 59) return 'Cinquenta e nove municípios'
  if (n === 159) return 'Cento e cinquenta e nove municípios'
  return `${n} municípios`
}

export function sliceBrand(years: readonly number[] = [SLICE_YEAR]): string {
  return `${sliceMunicipioPhrase(SLICE_MUNICIPIOS.length)} · ${sliceYearSpan(years)}`
}

export function sliceLabel(years: readonly number[] = [SLICE_YEAR]): string {
  return `${SLICE_CITIES} · ${sliceYearSpan(years)}`
}

export const SLICE_BRAND = sliceBrand([SLICE_YEAR])

export const SLICE_LABEL = sliceLabel([SLICE_YEAR])

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
  qsaEmpty: 'sem QSA na base',
} as const
