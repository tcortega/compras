import { DataTable, type Column } from '@/components/DataTable'
import { Pager } from '@/components/Pager'
import { Shell } from '@/components/Shell'
import { TriageFilters } from '@/components/TriageFilters'
import { listQueue } from '@/lib/api/flags'
import { formatDate } from '@/lib/format'
import { isFlagState, STATE_LABEL, triageCopy, type FlagQueueRow } from '@/lib/flags'
import { pageRequestFromSearch } from '@/lib/paging'
import { routes } from '@/lib/routes'
import { isStagingTriageEnabled } from '@/lib/staging'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Triagem interna',
  robots: { index: false, follow: false },
}

type Search = Record<string, string | string[] | undefined>

function first(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) return value[0]
  return value
}

const columns: Column<FlagQueueRow>[] = [
  {
    key: 'item',
    header: 'Item',
    cell: (row) => <a href={routes.triagemItem(row.id)}>{row.itemDescricao}</a>,
  },
  {
    key: 'orgao',
    header: 'Órgão',
    cell: (row) => row.orgaoRazaoSocial,
  },
  {
    key: 'kind',
    header: 'Tipo',
    mono: true,
    cell: (row) => row.kind,
  },
  {
    key: 'state',
    header: 'Estado',
    cell: (row) => STATE_LABEL[row.state],
  },
  {
    key: 'detected',
    header: 'Detectado',
    cell: (row) => formatDate(row.detectedAt),
  },
  {
    key: 'evidence',
    header: 'Evidência',
    cell: (row) =>
      row.sourceUrl ? (
        <a href={row.sourceUrl} rel="noreferrer">
          {triageCopy.evidence}
        </a>
      ) : (
        'n/d'
      ),
  },
]

export default async function TriagemPage({ searchParams }: { searchParams: Promise<Search> }) {
  if (!isStagingTriageEnabled()) notFound()

  const sp = await searchParams
  const req = pageRequestFromSearch(sp)
  const kind = first(sp.kind)?.trim() || undefined
  const stateRaw = first(sp.state)?.trim()
  const state = isFlagState(stateRaw) ? stateRaw : undefined
  const page = await listQueue({ skip: req.skip, take: req.take, kind, state })

  return (
    <Shell coverage={page.coverage}>
      <p className="kicker">{triageCopy.kicker}</p>
      <h1>{triageCopy.title}</h1>
      <p className="lede">{triageCopy.lede}</p>
      <div className="notice">
        <p>{triageCopy.framing}</p>
        <p>{triageCopy.hold}</p>
        <p>{triageCopy.precision}</p>
      </div>
      <TriageFilters kind={kind} state={state} />
      <DataTable
        rows={page.rows}
        columns={columns}
        coverage={page.coverage}
        footer={<Pager base={routes.triagem} req={req} total={page.total} extra={{ kind, state }} />}
      />
    </Shell>
  )
}
