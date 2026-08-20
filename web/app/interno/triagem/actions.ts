'use server'

import { applyFlagAction } from '@/lib/api/flags'
import { type FlagAction } from '@/lib/flags'
import { ApiError } from '@/lib/types'
import { redirect } from 'next/navigation'

const ACTIONS: FlagAction[] = ['review', 'notify', 'publish', 'resolve', 'retract']

function isAction(raw: string): raw is FlagAction {
  return ACTIONS.some((action) => action === raw)
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
