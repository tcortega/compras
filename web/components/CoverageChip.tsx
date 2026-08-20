import { coverageParts } from '@/lib/coverage'
import type { Coverage } from '@/lib/types'

export function CoverageChip({ coverage, className }: { coverage: Coverage; className?: string }) {
  const p = coverageParts(coverage)
  return (
    <span className={className ? `chip ${className}` : 'chip'}>
      <b>{p.n}</b>
      <span aria-hidden="true">·</span>
      <span>{p.geo}</span>
      <span aria-hidden="true">·</span>
      <span>{p.when}</span>
      <span aria-hidden="true">·</span>
      <span>{p.method}</span>
    </span>
  )
}
