'use client'

import { LABEL_RUBRIC, triageCopy, type FlagRecord, type LabelRubric } from '@/lib/flags'
import { useState } from 'react'

export function TriageLabels({ flag }: { flag: FlagRecord }) {
  const [notes, setNotes] = useState('')
  const [pending, setPending] = useState<LabelRubric | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  async function write(label: LabelRubric) {
    setPending(label)
    setMessage(null)
    const res = await fetch('/api/interno/labels', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        flag_id: flag.id,
        item_id: flag.itemId,
        label,
        evidence_url: flag.sourceUrl,
        notes,
        kind: flag.kind,
      }),
    })
    setPending(null)
    if (!res.ok) {
      setMessage('Não foi possível gravar o rótulo.')
      return
    }
    setMessage(triageCopy.labeled)
  }

  return (
    <section className="section" aria-labelledby="rotulos-triagem">
      <h2 id="rotulos-triagem">{triageCopy.labels}</h2>
      <p className="lede">{triageCopy.precision}</p>
      <label className="field field-grow">
        <span>{triageCopy.notes}</span>
        <input
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          maxLength={400}
          autoComplete="off"
        />
      </label>
      <div className="actions">
        {LABEL_RUBRIC.map((row) => (
          <button
            key={row.value}
            className="btn-ghost"
            type="button"
            disabled={pending != null}
            onClick={() => void write(row.value)}
          >
            {row.label}
          </button>
        ))}
      </div>
      {message ? (
        <p className="notice triage-flash" role="status">
          {message}
        </p>
      ) : null}
    </section>
  )
}
