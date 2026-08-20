import { Shell } from '@/components/Shell'
import { loadSliceYears } from '@/lib/api'
import type { Coverage } from '@/lib/types'
import type { ReactNode } from 'react'

export async function SliceShell({
  children,
  coverage,
  current,
  years,
}: {
  children: ReactNode
  coverage?: Coverage
  current?: string
  years?: readonly number[]
}) {
  const resolved = years ?? (await loadSliceYears())
  return (
    <Shell coverage={coverage} current={current} years={resolved}>
      {children}
    </Shell>
  )
}
