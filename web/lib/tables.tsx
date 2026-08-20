import { Money } from '@/components/Money'
import type { Column } from '@/components/DataTable'
import { formatCnpj, formatDate, formatDecimal, formatEsfera, formatSource } from '@/lib/format'
import { routes } from '@/lib/routes'
import type { Contratacao, Fornecedor, Item, Orgao } from '@/lib/types'

export const orgaoColumns: Column<Orgao>[] = [
  {
    key: 'nome',
    header: 'Razão social',
    cell: (row) => <a href={routes.orgao(row.id)}>{row.razaoSocial}</a>,
  },
  {
    key: 'cnpj',
    header: 'CNPJ',
    mono: true,
    cell: (row) => formatCnpj(row.cnpj),
  },
  {
    key: 'esfera',
    header: 'Esfera',
    cell: (row) => formatEsfera(row.esfera),
  },
  {
    key: 'uf',
    header: 'UF',
    cell: (row) => row.uf,
  },
  {
    key: 'municipio',
    header: 'Município',
    cell: (row) => row.municipioNome,
  },
]

export const fornecedorColumns: Column<Fornecedor>[] = [
  {
    key: 'nome',
    header: 'Razão social',
    cell: (row) => <a href={routes.fornecedor(row.id)}>{row.razaoSocial}</a>,
  },
  {
    key: 'cnpj',
    header: 'CNPJ',
    mono: true,
    cell: (row) => formatCnpj(row.cnpj),
  },
  {
    key: 'cnae',
    header: 'CNAE',
    mono: true,
    cell: (row) => row.cnae ?? 'n/d',
  },
  {
    key: 'opened',
    header: 'Abertura',
    cell: (row) => formatDate(row.openedOn),
  },
]

export const contratacaoColumns: Column<Contratacao>[] = [
  {
    key: 'objeto',
    header: 'Objeto',
    cell: (row) => <a href={routes.contratacao(row.id)}>{row.objeto}</a>,
  },
  {
    key: 'modalidade',
    header: 'Modalidade',
    cell: (row) => row.modalidade,
  },
  {
    key: 'ano',
    header: 'Ano',
    cell: (row) => row.ano,
  },
  {
    key: 'valor',
    header: 'Homologado',
    align: 'right',
    cell: (row) => <Money value={row.valorHomologado} />,
  },
  {
    key: 'fonte',
    header: 'Fonte',
    cell: (row) => formatSource(row.source),
  },
]

export const itemColumns: Column<Item>[] = [
  {
    key: 'desc',
    header: 'Descrição',
    cell: (row) => <a href={routes.item(row.id)}>{row.descricao}</a>,
  },
  {
    key: 'catmat',
    header: 'CATMAT',
    mono: true,
    cell: (row) => row.catmat ?? 'n/d',
  },
  {
    key: 'qty',
    header: 'Qtd',
    align: 'right',
    cell: (row) => formatDecimal(row.quantidade),
  },
  {
    key: 'un',
    header: 'Unidade',
    cell: (row) =>
      row.unidadeCanonica ? `${row.unidadeMedida} · ${row.unidadeCanonica}` : row.unidadeMedida,
  },
  {
    key: 'unit',
    header: 'Unitário',
    align: 'right',
    cell: (row) => <Money value={row.valorUnitario} />,
  },
  {
    key: 'total',
    header: 'Total',
    align: 'right',
    cell: (row) => <Money value={row.valorTotal} />,
  },
]
