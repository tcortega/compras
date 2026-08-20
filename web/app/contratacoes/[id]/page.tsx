import { DataTable } from '@/components/DataTable'
import { EntityHeader } from '@/components/EntityHeader'
import { FieldList } from '@/components/FieldList'
import { Money } from '@/components/Money'
import { Shell } from '@/components/Shell'
import { SourceLine } from '@/components/SourceLine'
import { Stat } from '@/components/Stat'
import { api, safeDetail } from '@/lib/api'
import { formatCnpj, formatDate, formatNumber, formatSource } from '@/lib/format'
import { routes } from '@/lib/routes'
import { itemColumns } from '@/lib/tables'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const revalidate = 3600
export const dynamicParams = true

export async function generateStaticParams() {
  const page = await api.listContratacoes({ skip: 0, take: 100 })
  return page.items.map((row) => ({ id: row.id }))
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params
  const row = await safeDetail(() => api.getContratacao(id))
  if (!row) return { title: 'Contratação não encontrada' }
  return {
    title: row.objeto.slice(0, 80),
    description: `${row.modalidade} · ${row.ano} · fonte ${row.source} · cobertura incompleta`,
  }
}

export default async function ContratacaoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const row = await safeDetail(() => api.getContratacao(id))
  if (!row) notFound()

  const [orgao, its] = await Promise.all([
    safeDetail(() => api.getOrgao(row.orgaoId)),
    api.listItems({ skip: 0, take: 50, contratacaoId: id }),
  ])

  return (
    <Shell coverage={its.coverage} current={routes.contratacoes}>
      <EntityHeader kicker={`Contratação · ${row.modalidade} · ${row.ano}`} title={row.objeto} />
      <FieldList
        fields={[
          {
            label: 'Órgão',
            value: orgao ? <a href={routes.orgao(orgao.id)}>{orgao.razaoSocial}</a> : 'n/d',
          },
          { label: 'CNPJ do órgão', value: orgao ? formatCnpj(orgao.cnpj) : 'n/d', mono: true },
          { label: 'PNCP', value: row.pncpId, mono: true },
          { label: 'Modalidade', value: row.modalidade },
          { label: 'Publicado em', value: formatDate(row.publicadoEm) },
          { label: 'Fonte', value: formatSource(row.source) },
        ]}
      />
      <div className="stats">
        <Stat label="Homologado" value={<Money value={row.valorHomologado} />} coverage={its.coverage} />
        <Stat label="Itens" value={formatNumber(its.total)} coverage={its.coverage} />
      </div>
      <SourceLine
        source={row.source}
        snapshotId={row.snapshotId}
        methodologyVersion={row.methodologyVersion}
        publishedAt={row.publicadoEm}
      />

      <section className="section">
        <div className="section-head">
          <h2>Itens</h2>
          <a href={`${routes.itens}?contratacaoId=${id}`}>Ver todos</a>
        </div>
        <DataTable rows={its.items} columns={itemColumns} coverage={its.coverage} />
      </section>
    </Shell>
  )
}
