import { DataTable } from '@/components/DataTable'
import { EntityHeader } from '@/components/EntityHeader'
import { FieldList } from '@/components/FieldList'
import { SliceShell } from '@/components/SliceShell'
import { SourceLine } from '@/components/SourceLine'
import { Stat } from '@/components/Stat'
import { api, safeDetail } from '@/lib/api'
import { copy } from '@/lib/copy'
import { formatCnpj, formatDate, formatNumber } from '@/lib/format'
import { routes } from '@/lib/routes'
import { contratacaoColumns, itemColumns } from '@/lib/tables'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const dynamic = 'force-dynamic'
export const dynamicParams = true

export async function generateStaticParams() {
  return []
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

  const qsa = row.qsa ?? []
  const idade =
    row.idadeCadastral && row.idadeCadastral !== copy.noValue && row.idadeAsOf
      ? `${row.idadeCadastral} (em ${formatDate(row.idadeAsOf)})`
      : (row.idadeCadastral ?? copy.noValue)

  const fields = [
    { label: 'CNPJ', value: formatCnpj(row.cnpj), mono: true },
    { label: 'CNAE', value: row.cnae ?? copy.noValue, mono: true },
    { label: 'Data de abertura', value: formatDate(row.openedOn) },
    { label: 'Idade cadastral', value: idade },
  ]
  if (row.cnaeDescricao) {
    fields.push({ label: 'CNAE descrição', value: row.cnaeDescricao, mono: false })
  }

  return (
    <SliceShell coverage={its.coverage} current={routes.fornecedores}>
      <EntityHeader kicker="Fornecedor · pessoa jurídica" title={row.razaoSocial} />
      <FieldList fields={fields} />
      <div className="stats">
        <Stat label="Contratações" value={formatNumber(cts.total)} coverage={cts.coverage} />
        <Stat label="Itens" value={formatNumber(its.total)} coverage={its.coverage} />
      </div>
      <SourceLine
        snapshotId={its.items[0]?.snapshotId}
        methodologyVersion={its.coverage.methodologyVersion}
      />

      <section className="section qsa">
        <div className="section-head">
          <h2>Quadro de sócios e administradores</h2>
        </div>
        {qsa.length === 0 ? (
          <p className="qsa-empty muted">{copy.qsaEmpty}</p>
        ) : (
          <div className="table-wrap">
            <table className="data qsa-table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>CPF</th>
                  <th>Qualificação</th>
                </tr>
              </thead>
              <tbody>
                {qsa.map((socio) => (
                  <tr key={`${socio.nome}:${socio.cpfMasked ?? ''}:${socio.qualificacao ?? ''}`}>
                    <td>{socio.nome}</td>
                    <td className="mono">{socio.cpfMasked ?? copy.noValue}</td>
                    <td>{socio.qualificacao ?? copy.noValue}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Contratações</h2>
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
    </SliceShell>
  )
}
