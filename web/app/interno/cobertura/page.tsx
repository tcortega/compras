import { SliceShell } from '@/components/SliceShell'
import { DataTable, type Column } from '@/components/DataTable'
import { loadCobertura } from '@/lib/api'
import { listFlagCounts } from '@/lib/api/flags'
import { copy } from '@/lib/copy'
import { coberturaInternaCopy, type DetectorKindCount } from '@/lib/flags'
import { formatDate, formatNumber } from '@/lib/format'
import { isStagingTriageEnabled } from '@/lib/staging'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Cobertura interna',
  robots: { index: false, follow: false },
}

const columns: Column<DetectorKindCount>[] = [
  {
    key: 'kind',
    header: 'Tipo',
    mono: true,
    cell: (row) => row.kind,
  },
  {
    key: 'n',
    header: 'n',
    align: 'right',
    cell: (row) => formatNumber(row.n),
  },
  {
    key: 'day',
    header: coberturaInternaCopy.day,
    cell: (row) => (row.day ? formatDate(row.day) : coberturaInternaCopy.emptyDay),
  },
]

export default async function CoberturaInternaPage() {
  if (!isStagingTriageEnabled()) notFound()

  const [payload, counts] = await Promise.all([loadCobertura(), listFlagCounts()])
  const yearsLabel = payload.years.length ? payload.years.join(', ') : copy.noValue

  return (
    <SliceShell coverage={payload.coverage} years={payload.years}>
      <p className="kicker">{coberturaInternaCopy.kicker}</p>
      <h1>{coberturaInternaCopy.title}</h1>
      <p className="lede">{coberturaInternaCopy.lede}</p>
      <div className="notice">
        <p>{copy.coverageIncomplete}</p>
        <p>{copy.coverageExempt}</p>
        <p>{copy.coverageQuality}</p>
        <p>{coberturaInternaCopy.framing}</p>
      </div>
      <section className="stats" aria-label="Números do recorte">
        <div className="stat">
          <p className="kicker">Municípios</p>
          <strong>{formatNumber(payload.municipios.n)}</strong>
        </div>
        <div className="stat">
          <p className="kicker">Anos</p>
          <strong>{yearsLabel}</strong>
        </div>
        <div className="stat">
          <p className="kicker">Itens</p>
          <strong>{formatNumber(payload.rows.items)}</strong>
        </div>
      </section>
      <section className="section">
        <div className="section-head">
          <h2>{coberturaInternaCopy.kinds}</h2>
          <span className="muted">{formatNumber(counts.total)} no warehouse</span>
        </div>
        <DataTable
          rows={counts.rows}
          columns={columns}
          coverage={counts.coverage}
          empty={coberturaInternaCopy.lede}
        />
      </section>
      <div className="prose">
        <p>Quando o recorte mistura UF, o agregado deixa UF vazia. Isso não é um total nacional.</p>
        <p>Homologado não entra no total de órgão nem de fornecedor.</p>
      </div>
    </SliceShell>
  )
}
