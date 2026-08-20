import { createFlag, listQueue } from '@/lib/api/flags'
import { jsonError, stagingOff } from '@/lib/api/http-error'
import { isStagingTriageEnabled } from '@/lib/staging'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET(req: Request) {
  if (!isStagingTriageEnabled()) return stagingOff()
  const url = new URL(req.url)
  const skip = Number.parseInt(url.searchParams.get('skip') ?? '0', 10)
  const take = Number.parseInt(url.searchParams.get('take') ?? '20', 10)
  try {
    const page = await listQueue({
      skip: Number.isFinite(skip) ? skip : 0,
      take: Number.isFinite(take) ? take : 20,
      kind: url.searchParams.get('kind') ?? undefined,
      state: url.searchParams.get('state') ?? undefined,
    })
    return NextResponse.json(page)
  } catch (err) {
    return jsonError(err)
  }
}

export async function POST(req: Request) {
  if (!isStagingTriageEnabled()) return stagingOff()
  try {
    const body = (await req.json()) as {
      itemId?: string
      kind?: string
      delta?: string
      sourceUrl?: string
      snapshotId?: string
      methodologyVersion?: string
    }
    const created = await createFlag({
      itemId: body.itemId ?? '',
      kind: body.kind ?? '',
      delta: body.delta ?? '',
      sourceUrl: body.sourceUrl ?? '',
      snapshotId: body.snapshotId ?? '',
      methodologyVersion: body.methodologyVersion ?? '',
    })
    return NextResponse.json(created, { status: 201 })
  } catch (err) {
    return jsonError(err)
  }
}
