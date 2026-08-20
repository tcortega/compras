import { loadRotulosView, saveRotulosLabel } from '@/lib/api/rotulos'
import { jsonError, stagingOff } from '@/lib/api/http-error'
import { isRubric } from '@/lib/rotulos'
import { isStagingTriageEnabled } from '@/lib/staging'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET(req: Request) {
  if (!isStagingTriageEnabled()) return stagingOff()
  try {
    const url = new URL(req.url)
    const raw = url.searchParams.get('at')
    const at = raw == null || raw === '' ? undefined : Number.parseInt(raw, 10)
    const view = await loadRotulosView(at)
    return NextResponse.json(view)
  } catch (err) {
    return jsonError(err)
  }
}

export async function POST(req: Request) {
  if (!isStagingTriageEnabled()) return stagingOff()
  try {
    const body = (await req.json()) as {
      packet_row_id?: string
      human_label?: string
      notes?: string
    }
    const packetRowId = (body.packet_row_id ?? '').trim()
    const humanLabel = body.human_label ?? ''
    if (!packetRowId || !isRubric(humanLabel)) {
      return NextResponse.json({ error: 'Pedido inválido' }, { status: 400 })
    }
    const view = await saveRotulosLabel({
      packetRowId,
      humanLabel,
      notes: body.notes ?? '',
    })
    return NextResponse.json(view)
  } catch (err) {
    return jsonError(err)
  }
}
