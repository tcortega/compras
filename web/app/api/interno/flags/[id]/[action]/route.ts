import { applyFlagAction } from '@/lib/api/flags'
import { parseAction } from '@/lib/api/flag-store'
import { jsonError, stagingOff } from '@/lib/api/http-error'
import { isStagingTriageEnabled } from '@/lib/staging'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string; action: string }> },
) {
  if (!isStagingTriageEnabled()) return stagingOff()
  try {
    const { id, action } = await params
    return NextResponse.json(await applyFlagAction(id, parseAction(action)))
  } catch (err) {
    return jsonError(err)
  }
}
