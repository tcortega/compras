import { coverageParts } from '@/lib/coverage'
import type { Coverage } from '@/lib/types'

export function CoverageChip({ coverage, className }: { coverage: Coverage; className?: string }) {
  const p = coverageParts(coverage)
  return (
    <span className={className ? `chip ${className}` : 'chip'}>
      <b>{p.n}</b>
      <span>{p.geo}</span>
      <span>{p.when}</span>
      <span>{p.method}</span>
    </span>
  )
}
