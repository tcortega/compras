import { EntityHeader } from '@/components/EntityHeader'
import { FieldList } from '@/components/FieldList'
import { Money } from '@/components/Money'
import { Shell } from '@/components/Shell'
import { SourceLine } from '@/components/SourceLine'
import { Stat } from '@/components/Stat'
import { api, safeDetail } from '@/lib/api'
import { formatCnpj, formatDecimal, formatMoney, formatQuarter } from '@/lib/format'
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

  const fornecedorId = row.fornecedorId
  const [ct, fornecedor, peers] = await Promise.all([
    safeDetail(() => api.getContratacao(row.contratacaoId)),
    fornecedorId ? safeDetail(() => api.getFornecedor(fornecedorId)) : Promise.resolve(null),
    api.listItems({ skip: 0, take: 1, uf: row.uf, quarter: row.quarter }),
  ])
  const orgao = ct ? await safeDetail(() => api.getOrgao(ct.orgaoId)) : null

  return (
    <Shell coverage={peers.coverage} current={routes.itens}>
      <EntityHeader kicker={`Item · ${row.uf} · ${formatQuarter(row.quarter)}`} title={row.descricao} />
      <FieldList
        fields={[
          {
            label: 'Contratação',
            value: ct ? <a href={routes.contratacao(ct.id)}>{ct.objeto}</a> : 'n/d',
          },
          {
            label: 'Órgão',
            value: orgao ? <a href={routes.orgao(orgao.id)}>{orgao.razaoSocial}</a> : 'n/d',
          },
          {
            label: 'Fornecedor',
            value: fornecedor ? (
              <a href={routes.fornecedor(fornecedor.id)}>{fornecedor.razaoSocial}</a>
            ) : (
              'n/d'
            ),
          },
          {
            label: 'CNPJ do fornecedor',
            value: fornecedor ? formatCnpj(fornecedor.cnpj) : 'n/d',
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
          label={`Quantidade (${row.unidadeMedida})`}
          value={formatDecimal(row.quantidade)}
          coverage={peers.coverage}
        />
        <Stat label="Valor unitário" value={<Money value={row.valorUnitario} />} coverage={peers.coverage} />
        <Stat label="Valor total" value={<Money value={row.valorTotal} />} coverage={peers.coverage} />
      </div>
      <p className="source">
        <span>
          Quantidade × unitário = {formatDecimal(row.quantidade)} × {formatMoney(row.valorUnitario)} = {formatMoney(row.valorTotal)}.
        </span>
        <span>
          O denominador acima (n, UF, trimestre) conta itens do mesmo UF e trimestre neste recorte, não o país.
        </span>
      </p>
      <SourceLine
        source={ct?.source}
        snapshotId={row.snapshotId}
        methodologyVersion={row.methodologyVersion}
      />
    </Shell>
  )
}
