import { CoverageChip } from '@/components/CoverageChip'
import type { Coverage } from '@/lib/types'
import type { ReactNode } from 'react'

export function Stat({
  label,
  value,
  coverage,
}: {
  label: string
  value: ReactNode
  coverage: Coverage
}) {
  return (
    <div className="stat">
      <p className="kicker">{label}</p>
      <strong>{value}</strong>
      <CoverageChip coverage={coverage} />
    </div>
  )
}
