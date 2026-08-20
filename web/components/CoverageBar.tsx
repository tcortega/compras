import { copy } from '@/lib/copy'
import { coverageText } from '@/lib/coverage'
import { routes } from '@/lib/routes'
import type { Coverage } from '@/lib/types'

export function CoverageBar({ coverage }: { coverage?: Coverage }) {
  return (
    <div className="coverage-bar">
      <div className="wrap coverage-bar-inner">
        <p>
          <strong>{copy.coverageIncomplete}</strong>
        </p>
        <p>
          {coverage ? `${coverageText(coverage)} · ` : null}
          <a href={routes.cobertura}>Como lemos a cobertura</a>
        </p>
      </div>
    </div>
  )
}
