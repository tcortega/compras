import { applyFlagAction } from '@/lib/api/flags'
import { jsonError, stagingOff } from '@/lib/api/http-error'
import { isStagingTriageEnabled } from '@/lib/staging'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function POST(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!isStagingTriageEnabled()) return stagingOff()
  try {
    const { id } = await params
    return NextResponse.json(await applyFlagAction(id, 'publish'))
  } catch (err) {
    return jsonError(err)
  }
}
