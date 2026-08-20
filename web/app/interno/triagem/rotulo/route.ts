import { appendTriageLabel } from '@/lib/api/labels'
import { LABEL_RUBRIC, type LabelRubric } from '@/lib/flags'
import { isStagingTriageEnabled } from '@/lib/staging'
import { notFound, redirect } from 'next/navigation'

export const dynamic = 'force-dynamic'

function isRubric(raw: string): raw is LabelRubric {
  return LABEL_RUBRIC.some((row) => row.value === raw)
}

export async function POST(req: Request) {
  if (!isStagingTriageEnabled()) notFound()
  const form = await req.formData()
  const id = String(form.get('id') ?? '')
  const itemId = String(form.get('itemId') ?? '')
  const kind = String(form.get('kind') ?? '')
  const evidence = String(form.get('evidence') ?? '')
  const notes = String(form.get('notes') ?? '')
  const label = String(form.get('label') ?? '')
  if (!id || !itemId || !isRubric(label)) redirect('/interno/triagem')
  await appendTriageLabel({
    flag_id: id,
    item_id: itemId,
    label,
    evidence_url: evidence,
    notes,
    kind,
  })
  redirect(`/interno/triagem/${id}?rotulo=1`)
}
