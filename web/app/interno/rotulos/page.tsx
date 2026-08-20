import { RotulosApp } from '@/components/RotulosApp'
import { Shell } from '@/components/Shell'
import { loadRotulosView } from '@/lib/api/rotulos'
import { rotulosCopy } from '@/lib/rotulos'
import { isStagingTriageEnabled } from '@/lib/staging'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: rotulosCopy.title,
  robots: { index: false, follow: false },
}

export default async function RotulosPage() {
  if (!isStagingTriageEnabled()) notFound()
  const initial = await loadRotulosView()
  return (
    <Shell>
      <RotulosApp initial={initial} />
    </Shell>
  )
}
