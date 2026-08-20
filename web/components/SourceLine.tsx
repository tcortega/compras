import { SNAPSHOT_ID } from '@/lib/copy'
import { formatDate, formatSource } from '@/lib/format'

export function SourceLine({
  source,
  snapshotId = SNAPSHOT_ID,
  methodologyVersion,
  publishedAt,
}: {
  source?: string
  snapshotId?: string
  methodologyVersion: string
  publishedAt?: string | null
}) {
  return (
    <p className="source">
        <span>Fonte: {source ? formatSource(source) : 'recorte ingerido'}</span>
      <span>
        Snapshot {snapshotId}
        {publishedAt ? ` · publicado em ${formatDate(publishedAt)}` : ''}
      </span>
      <span>Metodologia {methodologyVersion}</span>
    </p>
  )
}
