'use client'

import { ACTION_LABEL, actionsFor, triageCopy, type FlagAction, type FlagRecord } from '@/lib/flags'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export function TriageActions({ flag }: { flag: FlagRecord }) {
  const router = useRouter()
  const [pending, setPending] = useState<FlagAction | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const allowed = new Set(actionsFor(flag.state))

  async function run(action: FlagAction) {
    setPending(action)
    setMessage(null)
    const res = await fetch(`/api/interno/flags/${flag.id}/${action}`, { method: 'POST' })
    const body = (await res.json().catch(() => ({}))) as { error?: string; state?: string }
    setPending(null)
    if (res.status === 409 && /hold/i.test(body.error ?? '')) {
      setMessage(triageCopy.holdConflict)
      return
    }
    if (!res.ok) {
      setMessage(body.error ?? 'Não foi possível aplicar a transição.')
      return
    }
    router.refresh()
  }

  return (
    <div className="triage-actions">
      <div className="actions">
        {(['review', 'notify', 'publish', 'resolve', 'retract'] as const).map((action) => (
          <button
            key={action}
            className={action === 'publish' ? 'btn-ghost' : 'btn'}
            type="button"
            disabled={!allowed.has(action) || pending != null}
            onClick={() => void run(action)}
          >
            {ACTION_LABEL[action]}
          </button>
        ))}
      </div>
      {message ? (
        <p className="notice triage-flash" role="status">
          {message}
        </p>
      ) : null}
    </div>
  )
}
