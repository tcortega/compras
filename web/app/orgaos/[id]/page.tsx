import { DataTable } from '@/components/DataTable'
import { EntityHeader } from '@/components/EntityHeader'
import { FieldList } from '@/components/FieldList'
import { Shell } from '@/components/Shell'
import { SourceLine } from '@/components/SourceLine'
import { Stat } from '@/components/Stat'
import { api, safeDetail } from '@/lib/api'
import { formatCnpj, formatEsfera, formatNumber, formatPoder } from '@/lib/format'
import { routes } from '@/lib/routes'
import { contratacaoColumns, itemColumns } from '@/lib/tables'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const revalidate = 3600
export const dynamicParams = true

export async function generateStaticParams() {
  const page = await api.listOrgaos({ skip: 0, take: 100 })
  return page.items.map((row) => ({ id: row.id }))
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params
  const row = await safeDetail(() => api.getOrgao(id))
  if (!row) return { title: 'Órgão não encontrado' }
  return {
    title: row.razaoSocial,
    description: `${row.municipioNome}/${row.uf} · CNPJ ${formatCnpj(row.cnpj)} · cobertura incompleta`,
  }
}

export default async function OrgaoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const row = await safeDetail(() => api.getOrgao(id))
  if (!row) notFound()

  const [cts, its] = await Promise.all([
    api.listContratacoes({ skip: 0, take: 8, orgaoId: id }),
    api.listItems({ skip: 0, take: 8, orgaoId: id }),
  ])

  return (
    <Shell coverage={its.coverage} current={routes.orgaos}>
      <EntityHeader
        kicker={`Órgão · ${formatEsfera(row.esfera)} · ${formatPoder(row.poder)} · ${row.uf}`}
        title={row.razaoSocial}
      />
      <FieldList
        fields={[
          { label: 'CNPJ', value: formatCnpj(row.cnpj), mono: true },
          { label: 'Município', value: `${row.municipioNome} / ${row.uf}` },
          { label: 'IBGE', value: row.municipioIbge, mono: true },
          { label: 'Esfera / poder', value: `${formatEsfera(row.esfera)} · ${formatPoder(row.poder)}` },
        ]}
      />
      <div className="stats">
        <Stat label="Contratações" value={formatNumber(cts.total)} coverage={cts.coverage} />
        <Stat label="Itens" value={formatNumber(its.total)} coverage={its.coverage} />
      </div>
      <SourceLine methodologyVersion={its.coverage.methodologyVersion} />

      <section className="section">
        <div className="section-head">
          <h2>Contratações</h2>
          <a href={`${routes.contratacoes}?orgaoId=${id}`}>Ver todas</a>
        </div>
        <DataTable rows={cts.items} columns={contratacaoColumns} coverage={cts.coverage} />
      </section>
      <section className="section">
        <div className="section-head">
          <h2>Itens</h2>
          <a href={`${routes.itens}?orgaoId=${id}`}>Ver todos</a>
        </div>
        <DataTable rows={its.items} columns={itemColumns} coverage={its.coverage} />
      </section>
    </Shell>
  )
}
