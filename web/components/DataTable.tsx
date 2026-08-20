import { CoverageChip } from '@/components/CoverageChip'
import { copy } from '@/lib/copy'
import type { Coverage } from '@/lib/types'
import type { ReactNode } from 'react'

export type Column<T> = {
  key: string
  header: string
  align?: 'left' | 'right'
  mono?: boolean
  cell: (row: T) => ReactNode
}

function cellClass(col: { align?: 'left' | 'right'; mono?: boolean }): string | undefined {
  const parts = [col.align === 'right' ? 'num' : undefined, col.mono ? 'mono' : undefined]
  const joined = parts.filter(Boolean).join(' ')
  return joined || undefined
}

export function DataTable<T extends { id: string }>({
  rows,
  columns,
  coverage,
  footer,
}: {
  rows: T[]
  columns: Column<T>[]
  coverage: Coverage
  footer?: ReactNode
}) {
  if (rows.length === 0) {
    return (
      <div className="table-wrap">
        <p className="empty">{copy.empty}</p>
        <div className="table-foot">
          <CoverageChip coverage={coverage} />
          {footer}
        </div>
      </div>
    )
  }

  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={cellClass(col)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              {columns.map((col) => (
                <td key={col.key} className={cellClass(col)}>
                  {col.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="table-foot">
        <CoverageChip coverage={coverage} />
        {footer}
      </div>
    </div>
  )
}
