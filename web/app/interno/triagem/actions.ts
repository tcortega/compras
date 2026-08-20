'use server'

import { appendTriageLabel } from '@/lib/api/labels'
import { applyFlagAction } from '@/lib/api/flags'
import { LABEL_RUBRIC, type FlagAction, type LabelRubric } from '@/lib/flags'
import { ApiError } from '@/lib/types'
import { redirect } from 'next/navigation'

const ACTIONS: FlagAction[] = ['review', 'notify', 'publish', 'resolve', 'retract']

function isAction(raw: string): raw is FlagAction {
  return ACTIONS.some((action) => action === raw)
}

function isRubric(raw: string): raw is LabelRubric {
  return LABEL_RUBRIC.some((row) => row.value === raw)
}

export async function runTriageAction(formData: FormData) {
  const id = String(formData.get('id') ?? '')
  const action = String(formData.get('action') ?? '')
  if (!id || !isAction(action)) redirect('/interno/triagem')
  try {
    await applyFlagAction(id, action)
  } catch (err) {
    if (err instanceof ApiError && err.status === 409 && /hold/i.test(err.message)) {
      redirect(`/interno/triagem/${id}?erro=carencia`)
    }
    redirect(`/interno/triagem/${id}?erro=transicao`)
  }
  redirect(`/interno/triagem/${id}`)
}

export async function runTriageLabel(formData: FormData) {
  const id = String(formData.get('id') ?? '')
  const itemId = String(formData.get('itemId') ?? '')
  const kind = String(formData.get('kind') ?? '')
  const evidence = String(formData.get('evidence') ?? '')
  const notes = String(formData.get('notes') ?? '')
  const label = String(formData.get('label') ?? '')
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
