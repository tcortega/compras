import { appendTriageLabel, readTriageLabels } from '@/lib/api/labels'
import { jsonError, stagingOff } from '@/lib/api/http-error'
import { LABEL_RUBRIC, type LabelRubric } from '@/lib/flags'
import { isStagingTriageEnabled } from '@/lib/staging'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

function isRubric(raw: string): raw is LabelRubric {
  return LABEL_RUBRIC.some((row) => row.value === raw)
}

export async function GET() {
  if (!isStagingTriageEnabled()) return stagingOff()
  try {
    const items = await readTriageLabels()
    return NextResponse.json({ items, total: items.length })
  } catch (err) {
    return jsonError(err)
  }
}

export async function POST(req: Request) {
  if (!isStagingTriageEnabled()) return stagingOff()
  try {
    const body = (await req.json()) as {
      flag_id?: string
      item_id?: string
      label?: string
      evidence_url?: string
      notes?: string
      kind?: string
    }
    const label = body.label ?? ''
    if (!isRubric(label) || !body.flag_id || !body.item_id) {
      return NextResponse.json({ error: 'Pedido inválido' }, { status: 400 })
    }
    const row = await appendTriageLabel({
      flag_id: body.flag_id,
      item_id: body.item_id,
      label,
      evidence_url: body.evidence_url ?? '',
      notes: body.notes ?? '',
      kind: body.kind ?? '',
    })
    return NextResponse.json(row, { status: 201 })
  } catch (err) {
    return jsonError(err)
  }
}
