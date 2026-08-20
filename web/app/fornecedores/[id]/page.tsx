import { DataTable } from '@/components/DataTable'
import { EntityHeader } from '@/components/EntityHeader'
import { FieldList } from '@/components/FieldList'
import { Money } from '@/components/Money'
import { Shell } from '@/components/Shell'
import { SourceLine } from '@/components/SourceLine'
import { Stat } from '@/components/Stat'
import { api, safeDetail } from '@/lib/api'
import { METHOD_VERSION } from '@/lib/copy'
import { formatCnpj, formatDate, formatNumber } from '@/lib/format'
import { routes } from '@/lib/routes'
import { contratacaoColumns, itemColumns } from '@/lib/tables'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const revalidate = 3600
export const dynamicParams = true

export async function generateStaticParams() {
  const page = await api.listFornecedores({ skip: 0, take: 100 })
  return page.items.map((row) => ({ id: row.id }))
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

  return (
    <Shell coverage={row.coverage} current={routes.fornecedores}>
      <EntityHeader kicker="Fornecedor · pessoa jurídica" title={row.razaoSocial} />
      <FieldList
        fields={[
          { label: 'CNPJ', value: formatCnpj(row.cnpj), mono: true },
          { label: 'CNAE', value: row.cnae ?? 'n/d', mono: true },
          { label: 'Abertura', value: formatDate(row.openedOn) },
          { label: 'Itens no recorte', value: formatNumber(row.totals.items) },
        ]}
      />
      <div className="stats">
        <Stat label="Contratações" value={formatNumber(row.totals.contratacoes)} coverage={row.totals.coverage} />
        <Stat label="Homologado" value={<Money value={row.totals.valorHomologado} />} coverage={row.totals.coverage} />
        <Stat label="Itens" value={formatNumber(row.totals.items)} coverage={row.totals.coverage} />
      </div>
      <SourceLine methodologyVersion={METHOD_VERSION} />

      <section className="section">
        <div className="section-head">
          <h2>Contratações neste recorte</h2>
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
