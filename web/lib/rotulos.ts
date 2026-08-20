import { LABEL_RUBRIC, type LabelRubric } from '@/lib/flags'

export const ROTULOS_PACKETS = [
  { slug: 'vr-30', file: 'vr-30-blind.csv', optional: false },
  { slug: 'bauru-30', file: 'bauru-30-blind.csv', optional: false },
  { slug: 'b5-50', file: 'b5-50-blind.csv', optional: false },
  { slug: 'caxias-50', file: 'caxias-50-blind.csv', optional: true },
] as const

export type RotulosPacketSlug = (typeof ROTULOS_PACKETS)[number]['slug']

export const KEY_FILE_MARK = 'keys-do-not-give-to-human'

export const ROTULOS_PEER_LIMIT = 3

export const AGREEMENT_HEADER =
  'packet_row_id,packet,city,ibge,year,id_compra_item,ID_contratacao_PNCP,numero_item,human_label,notes,labeled_at'

export const BLIND_COLUMNS = [
  'packet_row_id',
  'city',
  'ibge',
  'year',
  'id_compra',
  'id_compra_item',
  'ID_contratacao_PNCP',
  'numero_item',
  'descricao',
  'unidade_medida',
  'quantidade',
  'valor_unitario_estimado',
  'valor_unitario_resultado',
  'valor_total',
  'valor_total_resultado',
  'catalog_code',
  'source_doc_url',
  'pncp_item_api_url',
  'official_compra_url',
  'official_item_url',
] as const

export type BlindItem = {
  packet: RotulosPacketSlug
  packetRowId: string
  city: string
  ibge: string
  year: string
  idCompra: string
  idCompraItem: string
  idContratacaoPncp: string
  numeroItem: string
  descricao: string
  unidadeMedida: string
  quantidade: string
  valorUnitarioEstimado: string
  valorUnitarioResultado: string
  valorTotal: string
  valorTotalResultado: string
  catalogCode: string
  sourceDocUrl: string
  pncpItemApiUrl: string
  officialCompraUrl: string
  officialItemUrl: string
}

export type PeerPurchase = {
  descricao: string
  unidadeMedida: string
  valorUnitario: string
}

export type PeerGroup = {
  medianUnitPrice: string
  peers: PeerPurchase[]
}

export type HumanLabelRow = {
  packetRowId: string
  packet: RotulosPacketSlug
  city: string
  ibge: string
  year: string
  idCompraItem: string
  idContratacaoPncp: string
  numeroItem: string
  humanLabel: LabelRubric
  notes: string
  labeledAt: string
}

export type RotulosView = {
  total: number
  position: number
  done: boolean
  item: BlindItem | null
  existingLabel: LabelRubric | null
  existingNotes: string
  medianUnitPrice: string
  peers: PeerPurchase[]
}

export const rotulosCopy = {
  kicker: 'Revisão interna',
  title: 'Conferir item',
  lede: 'O computador já marcou este preço como alto frente a itens semelhantes. Abra o link oficial. Depois escolha o porquê.',
  howto:
    'Conferir o item na fonte: compare unidade, quantidade e preço unitário, depois pressione 1 a 4.',
  empty: 'Nenhum item para conferir neste recorte.',
  done: 'Todos os itens deste recorte foram conferidos.',
  notes: 'Notas',
  skip: 'Pular',
  back: 'Voltar',
  saveError: 'Não foi possível gravar o rótulo.',
  progress: (position: number, total: number) => `${position} de ${total}`,
  unit: 'Unidade',
  quantity: 'Quantidade',
  unitEstimate: 'Unitário estimado',
  unitResult: 'Unitário resultado',
  total: 'Total',
  totalResult: 'Total resultado',
  catalog: 'Código do catálogo',
  sourceDoc: 'Documento de origem',
  pncpApi: 'API do item',
  officialCompra: 'Compra oficial',
  officialItem: 'Item oficial',
  sources: 'Fontes',
  peers: 'Outras compras usadas na comparação',
  noPeers: 'sem pares neste recorte',
  peerMedian: 'Mediana do grupo',
  peerPrice: 'Unitário',
  hints: {
    real: 'Mesmo produto, mesmo pacote, e o preço oficial bate com a linha. Eles de fato pagaram isso.',
    'unit error':
      'O tamanho do pacote não é o da comparação (ex.: isto é Pacote 10, os pares são 1 fita).',
    'spec difference': 'Não é o mesmo produto do grupo de comparação.',
    'data error':
      'Não houve adjudicação de verdade, ou o número oficial não é o da linha (fracassado, deserto, cancelado, CSV errado).',
  },
} as const

export function isRubric(raw: string): raw is LabelRubric {
  return LABEL_RUBRIC.some((row) => row.value === raw)
}

export function isPacketSlug(raw: string): raw is RotulosPacketSlug {
  return ROTULOS_PACKETS.some((row) => row.slug === raw)
}

export function emptyPeerGroup(): PeerGroup {
  return { medianUnitPrice: '', peers: [] }
}

export function emptyRotulosView(): RotulosView {
  return {
    total: 0,
    position: 0,
    done: true,
    item: null,
    existingLabel: null,
    existingNotes: '',
    ...emptyPeerGroup(),
  }
}
