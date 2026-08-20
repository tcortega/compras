import { mkdir, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'

export const ROTULOS_DATA_DIR = '/tmp/compras-rotulos-e2e'
export const ROTULOS_LEAK = 'LEAKED_KEY_TOKEN_DO_NOT_SHOW'

const HEADER =
  'packet_row_id,city,ibge,year,id_compra,id_compra_item,ID_contratacao_PNCP,numero_item,descricao,unidade_medida,quantidade,valor_unitario_estimado,valor_unitario_resultado,valor_total,valor_total_resultado,catalog_code,source_doc_url,pncp_item_api_url,official_compra_url,official_item_url'

export const PEER_HEADING = 'Outras compras usadas na comparação'
export const PEER_EMPTY = 'sem pares neste recorte'
export const PEER_MEDIAN = '18.40'
export const PEER_EXTRA = 'PEER EXTRA NAO MOSTRAR'

export const SYNTHETIC_PEERS = [
  {
    descricao: 'Papel sulfite A4 75g 500 folhas',
    unidade_medida: 'UN',
    valor_unitario: '19.90',
  },
  {
    descricao: 'Resma chamex A4 75g',
    unidade_medida: 'UN',
    valor_unitario: '17.20',
  },
  {
    descricao: 'Papel A4 alcalino 75g',
    unidade_medida: 'PCT',
    valor_unitario: '18.10',
  },
] as const

export const SYNTHETIC_ITEMS = [
  {
    packet_row_id: 'syn-row-001',
    descricao: 'Resma de papel A4 75g',
    official_item_url: 'https://pncp.gov.br/app/editais/0000001/2024/1#item-1',
  },
  {
    packet_row_id: 'syn-row-002',
    descricao: 'Caneta esferográfica azul',
    official_item_url: 'https://pncp.gov.br/app/editais/0000001/2024/2#item-1',
  },
  {
    packet_row_id: 'syn-row-003',
    descricao: 'Pasta suspensa cartonada',
    official_item_url: 'https://pncp.gov.br/app/editais/0000001/2024/3#item-1',
  },
  {
    packet_row_id: 'syn-row-004',
    descricao: 'Clips n. 2/0 caixa',
    official_item_url: '',
  },
] as const

function line(item: (typeof SYNTHETIC_ITEMS)[number], index: number): string {
  const n = index + 1
  return [
    item.packet_row_id,
    'Cidade Alfa',
    '0000001',
    '2024',
    `compra-syn-${n}`,
    `item-syn-${n}`,
    `00000000000000-1-00000${n}/2024`,
    String(n),
    item.descricao,
    'UN',
    '100',
    '25.00',
    '24.50',
    '2500.00',
    '2450.00',
    '369114',
    `https://pncp.gov.br/app/editais/0000001/2024/${n}`,
    `https://pncp.gov.br/api/pncp/v1/orgaos/00000000000000/compras/2024/${n}/itens/1`,
    `https://pncp.gov.br/app/editais/0000001/2024/${n}`,
    item.official_item_url,
  ].join(',')
}

export async function plantRotulosFixtures(): Promise<void> {
  const adjudication = path.join(ROTULOS_DATA_DIR, 'labels', 'adjudication')
  const agreement = path.join(adjudication, 'agreement')
  const peers = path.join(adjudication, 'peers')
  await rm(agreement, { recursive: true, force: true })
  await mkdir(peers, { recursive: true })
  await writeFile(
    path.join(adjudication, 'vr-30-blind.csv'),
    `${HEADER}\n${SYNTHETIC_ITEMS.map(line).join('\n')}\n`,
    'utf8',
  )
  await writeFile(
    path.join(adjudication, 'vr-30-keys-do-not-give-to-human.csv'),
    `packet_row_id,hidden_label,score,kind\nsyn-row-001,${ROTULOS_LEAK},0.99,cnae_mismatch\n`,
    'utf8',
  )
  await writeFile(
    path.join(peers, 'vr-30-keys-do-not-give-to-human.json'),
    JSON.stringify({
      'syn-row-001': {
        median_unit_price: '0.99',
        peers: [{ descricao: ROTULOS_LEAK, unidade_medida: 'score', valor_unitario: '0.99' }],
      },
    }),
    'utf8',
  )
  await writeFile(
    path.join(peers, 'vr-30-peers.json'),
    JSON.stringify({
      'syn-row-001': {
        median_unit_price: PEER_MEDIAN,
        score: '0.99',
        rank: '1',
        z: '4.2',
        hidden_label: ROTULOS_LEAK,
        peers: [
          ...SYNTHETIC_PEERS,
          { descricao: PEER_EXTRA, unidade_medida: 'UN', valor_unitario: '99.00' },
        ],
      },
      'syn-row-003': { median_unit_price: '', peers: [] },
    }),
    'utf8',
  )
}

export function agreementFile(): string {
  return path.join(ROTULOS_DATA_DIR, 'labels', 'adjudication', 'agreement', 'vr-30-human.csv')
}
