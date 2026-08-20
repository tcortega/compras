import { formatDate, formatSource } from '@/lib/format'

export function SourceLine({
  source,
  snapshotId,
  methodologyVersion,
  publishedAt,
}: {
  source?: string
  snapshotId?: string | null
  methodologyVersion: string
  publishedAt?: string | null
}) {
  return (
    <p className="source">
      <span>Fonte: {source ? formatSource(source) : 'recorte ingerido'}</span>
      {snapshotId ? (
        <span>
          Snapshot {snapshotId}
          {publishedAt ? ` · publicado em ${formatDate(publishedAt)}` : ''}
        </span>
      ) : publishedAt ? (
        <span>Publicado em {formatDate(publishedAt)}</span>
      ) : null}
      <span>Metodologia {methodologyVersion}</span>
    </p>
  )
}
