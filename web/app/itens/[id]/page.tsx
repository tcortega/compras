import { EntityHeader } from '@/components/EntityHeader'
import { FieldList } from '@/components/FieldList'
import { Money } from '@/components/Money'
import { Shell } from '@/components/Shell'
import { SourceLine } from '@/components/SourceLine'
import { Stat } from '@/components/Stat'
import { api, safeDetail } from '@/lib/api'
import { formatCnpj, formatDecimal, formatNumber, formatQuarter } from '@/lib/format'
import { routes } from '@/lib/routes'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const revalidate = 3600
export const dynamicParams = true

export async function generateStaticParams() {
  const page = await api.listItems({ skip: 0, take: 100 })
  return page.items.map((row) => ({ id: row.id }))
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params
  const row = await safeDetail(() => api.getItem(id))
  if (!row) return { title: 'Item não encontrado' }
  return {
    title: row.descricao,
    description: `${row.uf} · ${row.quarter} · cobertura incompleta`,
  }
}

export default async function ItemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const row = await safeDetail(() => api.getItem(id))
  if (!row) notFound()

  return (
    <Shell coverage={row.coverage} current={routes.itens}>
      <EntityHeader kicker={`Item · ${row.uf} · ${formatQuarter(row.quarter)}`} title={row.descricao} />
      <FieldList
        fields={[
          {
            label: 'Contratação',
            value: <a href={routes.contratacao(row.contratacao.id)}>{row.contratacao.objeto}</a>,
          },
          {
            label: 'Órgão',
            value: <a href={routes.orgao(row.orgao.id)}>{row.orgao.razaoSocial}</a>,
          },
          {
            label: 'Fornecedor',
            value: row.fornecedor ? (
              <a href={routes.fornecedor(row.fornecedor.id)}>{row.fornecedor.razaoSocial}</a>
            ) : (
              'n/d'
            ),
          },
          {
            label: 'CNPJ do fornecedor',
            value: row.fornecedor ? formatCnpj(row.fornecedor.cnpj) : 'n/d',
            mono: true,
          },
          { label: 'CATMAT', value: row.catmat ?? 'n/d', mono: true },
          { label: 'CATSER', value: row.catser ?? 'n/d', mono: true },
          { label: 'Unidade original', value: row.unidadeMedida },
          { label: 'Unidade canônica', value: row.unidadeCanonica ?? 'n/d' },
        ]}
      />
      <div className="stats">
        <Stat
          label="Quantidade"
          value={`${formatNumber(row.quantidade)} ${row.unidadeMedida}`}
          coverage={row.coverage}
        />
        <Stat label="Valor unitário" value={<Money value={row.valorUnitario} />} coverage={row.coverage} />
        <Stat label="Valor total" value={<Money value={row.valorTotal} />} coverage={row.coverage} />
      </div>
      <p className="source">
        <span>
          Quantidade × unitário = {formatDecimal(row.quantidade)} × {row.valorUnitario ?? 'n/d'} = {row.valorTotal ?? 'n/d'}.
        </span>
        <span>
          O denominador acima (n, UF, trimestre) conta itens do mesmo UF e trimestre neste recorte, não o país.
        </span>
      </p>
      <SourceLine
        source={row.contratacao.source}
        snapshotId={row.snapshotId}
        methodologyVersion={row.methodologyVersion}
      />
    </Shell>
  )
}
