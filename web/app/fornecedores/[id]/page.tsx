import { DataTable } from '@/components/DataTable'
import { EntityHeader } from '@/components/EntityHeader'
import { FieldList } from '@/components/FieldList'
import { Money } from '@/components/Money'
import { Shell } from '@/components/Shell'
import { SourceLine } from '@/components/SourceLine'
import { Stat } from '@/components/Stat'
import { api, safeDetail } from '@/lib/api'
import { METHOD_VERSION } from '@/lib/copy'
import { explorerDynamic, explorerRevalidate, staticEntityIds } from '@/lib/rendering'
import { formatCnpj, formatDate, formatNumber } from '@/lib/format'
import { routes } from '@/lib/routes'
import { contratacaoColumns, itemColumns } from '@/lib/tables'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const dynamic = explorerDynamic
export const revalidate = explorerRevalidate
export const dynamicParams = true

export async function generateStaticParams() {
  return staticEntityIds(() => api.listFornecedores({ skip: 0, take: 100 }))
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params
  const row = await safeDetail(() => api.getFornecedor(id))
  if (!row) return { title: 'Fornecedor não encontrado' }
  return {
    title: row.razaoSocial,
    description: `CNPJ ${formatCnpj(row.cnpj)} · cobertura incompleta`,
  }
}

export default async function FornecedorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const row = await safeDetail(() => api.getFornecedor(id))
  if (!row) notFound()

  const [its, cts] = await Promise.all([
    api.listItems({ skip: 0, take: 12, fornecedorId: id }),
    api.listContratacoes({ skip: 0, take: 8, fornecedorId: id }),
  ])
  const homologado = cts.items
    .map((c) => c.valorHomologado)
    .filter((v): v is number => v != null)
    .reduce<number | null>((sum, v) => (sum == null ? v : sum + v), null)

  return (
    <Shell coverage={its.coverage} current={routes.fornecedores}>
      <EntityHeader kicker="Fornecedor · pessoa jurídica" title={row.razaoSocial} />
      <FieldList
        fields={[
          { label: 'CNPJ', value: formatCnpj(row.cnpj), mono: true },
          { label: 'CNAE', value: row.cnae ?? 'n/d', mono: true },
          { label: 'Abertura', value: formatDate(row.openedOn) },
        ]}
      />
      <div className="stats">
        <Stat label="Contratações" value={formatNumber(cts.total)} coverage={cts.coverage} />
        <Stat label="Homologado" value={<Money value={homologado} />} coverage={cts.coverage} />
        <Stat label="Itens" value={formatNumber(its.total)} coverage={its.coverage} />
      </div>
      <SourceLine methodologyVersion={METHOD_VERSION} />

      <section className="section">
        <div className="section-head">
          <h2>Contratações neste recorte</h2>
          <a href={`${routes.contratacoes}?fornecedorId=${id}`}>Ver todas</a>
        </div>
        <DataTable rows={cts.items} columns={contratacaoColumns} coverage={cts.coverage} />
      </section>
      <section className="section">
        <div className="section-head">
          <h2>Itens</h2>
          <a href={`${routes.itens}?fornecedorId=${id}`}>Ver todos</a>
        </div>
        <DataTable rows={its.items} columns={itemColumns} coverage={its.coverage} />
      </section>
    </Shell>
  )
}
