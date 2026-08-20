import { EntityHeader } from '@/components/EntityHeader'
import { FieldList } from '@/components/FieldList'
import { Shell } from '@/components/Shell'
import { TriageActions } from '@/components/TriageActions'
import { TriageLabels } from '@/components/TriageLabels'
import { loadSliceCoverage, safeDetail } from '@/lib/api'
import { enrichFlags, getFlag, listFlagAudit } from '@/lib/api/flags'
import { formatDate } from '@/lib/format'
import { isFlagState, STATE_LABEL, triageCopy } from '@/lib/flags'
import { routes } from '@/lib/routes'
import { isStagingTriageEnabled } from '@/lib/staging'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const dynamic = 'force-dynamic'
export const dynamicParams = true

export async function generateStaticParams() {
  return []
}

export const metadata: Metadata = {
  title: 'Indício interno',
  robots: { index: false, follow: false },
}

export default async function TriagemItemPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>
  searchParams: Promise<Record<string, string | string[] | undefined>>
}) {
  if (!isStagingTriageEnabled()) notFound()
  const { id } = await params
  const query = await searchParams
  const erro = Array.isArray(query.erro) ? query.erro[0] : query.erro
  const rotulo = Array.isArray(query.rotulo) ? query.rotulo[0] : query.rotulo
  const flag = await safeDetail(() => getFlag(id))
  if (!flag) notFound()

  const [coverage, [row], audit] = await Promise.all([
    loadSliceCoverage(),
    enrichFlags([flag]),
    listFlagAudit(flag.id).catch(() => []),
  ])
  const item = row ?? {
    ...flag,
    itemDescricao: 'n/d',
    orgaoRazaoSocial: 'n/d',
  }

  return (
    <Shell coverage={coverage}>
      <p className="kicker">{triageCopy.kicker}</p>
      <EntityHeader kicker={triageCopy.framing} title={item.itemDescricao} />
      <p className="lede">{triageCopy.lede}</p>
      <FieldList
        fields={[
          { label: 'Órgão', value: item.orgaoRazaoSocial },
          { label: 'Tipo', value: flag.kind, mono: true },
          { label: 'Estado', value: STATE_LABEL[flag.state] },
          { label: 'Detectado', value: formatDate(flag.detectedAt) },
          { label: 'Notificado', value: formatDate(flag.notifiedAt) },
          { label: triageCopy.notifyArtifact, value: flag.notifyArtifact || 'n/d' },
          { label: 'Publicável após', value: formatDate(flag.publishAfter) },
          { label: 'Publicado', value: formatDate(flag.publishedAt) },
          {
            label: 'Evidência',
            value: flag.sourceUrl ? (
              <a href={flag.sourceUrl} rel="noreferrer">
                {triageCopy.evidence}
              </a>
            ) : (
              'n/d'
            ),
          },
          { label: 'Delta', value: flag.delta },
        ]}
      />
      <TriageActions flag={flag} />
      {erro === 'carencia' ? (
        <p className="notice triage-flash" role="status">
          {triageCopy.holdConflict}
        </p>
      ) : null}
      {erro === 'transicao' ? (
        <p className="notice triage-flash" role="status">
          {triageCopy.transitionConflict}
        </p>
      ) : null}
      {rotulo === '1' ? (
        <p className="notice triage-flash" role="status">
          {triageCopy.labeled}
        </p>
      ) : null}
      <section className="section" aria-labelledby="trilha-estados">
        <h2 id="trilha-estados">{audit.length > 0 ? triageCopy.audit : triageCopy.timestamps}</h2>
        {audit.length > 0 ? (
          <ol className="audit-list">
            {audit.map((entry) => (
              <li key={entry.id}>
                <span className="kicker">
                  {entry.fromState && isFlagState(entry.fromState)
                    ? STATE_LABEL[entry.fromState]
                    : 'criação'}
                  {' para '}
                  {isFlagState(entry.toState) ? STATE_LABEL[entry.toState] : entry.toState}
                </span>
                <span>{formatDate(entry.at)}</span>
                <span className="muted">{entry.actor}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="muted">
            Detectado {formatDate(flag.detectedAt)}. Notificado {formatDate(flag.notifiedAt)}. Publicado{' '}
            {formatDate(flag.publishedAt)}.
          </p>
        )}
      </section>
      <TriageLabels flag={flag} />
      <p className="actions">
        <a className="btn-ghost" href={routes.triagem}>
          Voltar à fila
        </a>
        <a className="btn-ghost" href={routes.item(flag.itemId)}>
          Ver item no explorador
        </a>
      </p>
    </Shell>
  )
}
