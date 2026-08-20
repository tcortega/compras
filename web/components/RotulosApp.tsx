'use client'

import { FieldList } from '@/components/FieldList'
import { Money } from '@/components/Money'
import { LABEL_RUBRIC, type LabelRubric } from '@/lib/flags'
import { formatDecimal } from '@/lib/format'
import { rotulosCopy, type BlindItem, type RotulosView } from '@/lib/rotulos'
import { useCallback, useEffect, useRef, useState } from 'react'

function sourceLinks(item: BlindItem) {
  return [
    { href: item.sourceDocUrl, label: rotulosCopy.sourceDoc },
    { href: item.pncpItemApiUrl, label: rotulosCopy.pncpApi },
    { href: item.officialCompraUrl, label: rotulosCopy.officialCompra },
    { href: item.officialItemUrl, label: rotulosCopy.officialItem },
  ].filter((row) => row.href.length > 0)
}

async function readView(at?: number): Promise<RotulosView> {
  const qs = at == null ? '' : `?at=${at}`
  const res = await fetch(`/api/interno/rotulos${qs}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(rotulosCopy.saveError)
  return (await res.json()) as RotulosView
}

export function RotulosApp({ initial }: { initial: RotulosView }) {
  const [view, setView] = useState(initial)
  const [notes, setNotes] = useState(initial.existingNotes)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const notesRef = useRef(notes)
  const pendingRef = useRef(false)
  const viewRef = useRef(view)

  useEffect(() => {
    notesRef.current = notes
  }, [notes])

  useEffect(() => {
    pendingRef.current = pending
  }, [pending])

  useEffect(() => {
    viewRef.current = view
  }, [view])

  const applyView = useCallback((next: RotulosView) => {
    setView(next)
    setNotes(next.existingNotes)
    setError(null)
  }, [])

  const goTo = useCallback(
    async (at?: number) => {
      if (pendingRef.current) return
      setPending(true)
      try {
        applyView(await readView(at))
      } catch {
        setError(rotulosCopy.saveError)
      } finally {
        setPending(false)
      }
    },
    [applyView],
  )

  const label = useCallback(
    async (humanLabel: LabelRubric) => {
      const current = viewRef.current.item
      if (!current || pendingRef.current) return
      setPending(true)
      try {
        const res = await fetch('/api/interno/rotulos', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            packet_row_id: current.packetRowId,
            human_label: humanLabel,
            notes: notesRef.current,
          }),
        })
        if (!res.ok) throw new Error(rotulosCopy.saveError)
        applyView((await res.json()) as RotulosView)
      } catch {
        setError(rotulosCopy.saveError)
      } finally {
        setPending(false)
      }
    },
    [applyView],
  )

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.metaKey || event.ctrlKey || event.altKey) return
      const target = event.target
      if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) return
      const map: Record<string, LabelRubric | undefined> = {
        '1': 'real',
        '2': 'unit error',
        '3': 'spec difference',
        '4': 'data error',
      }
      const picked = map[event.key]
      if (!picked) return
      event.preventDefault()
      void label(picked)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [label])

  const item = view.item
  const links = item ? sourceLinks(item) : []
  const canBack = view.total > 0 && (view.position > 1 || view.done)
  const canSkip = Boolean(item)

  return (
    <div className="rotulos-page">
      <div className="rotulos-head">
        <p className="kicker">{rotulosCopy.kicker}</p>
        {view.total > 0 ? (
          <p className="rotulos-progress" aria-live="polite">
            {rotulosCopy.progress(view.done ? view.total : view.position, view.total)}
          </p>
        ) : null}
      </div>
      <p className="lede">{rotulosCopy.lede}</p>
      <p className="rotulos-howto">{rotulosCopy.howto}</p>
      {error ? (
        <p className="notice triage-flash" role="alert">
          {error}
        </p>
      ) : null}
      {item ? (
        <article className="rotulos-card">
          <p className="kicker">
            {item.packet} · {item.city} · {item.year}
          </p>
          <h1>{item.descricao || rotulosCopy.title}</h1>
          <FieldList
            fields={[
              { label: rotulosCopy.unit, value: item.unidadeMedida },
              { label: rotulosCopy.quantity, value: formatDecimal(item.quantidade) },
              { label: rotulosCopy.unitEstimate, value: <Money value={item.valorUnitarioEstimado} /> },
              { label: rotulosCopy.unitResult, value: <Money value={item.valorUnitarioResultado} /> },
              { label: rotulosCopy.total, value: <Money value={item.valorTotal} /> },
              { label: rotulosCopy.totalResult, value: <Money value={item.valorTotalResultado} /> },
              { label: rotulosCopy.catalog, value: item.catalogCode || 'n/d', mono: true },
            ]}
          />
          {links.length > 0 ? (
            <nav className="rotulos-sources" aria-label={rotulosCopy.sources}>
              {links.map((row) => (
                <a key={row.label} href={row.href} target="_blank" rel="noreferrer">
                  {row.label}
                </a>
              ))}
            </nav>
          ) : null}
          <div className="rotulos-prompt">
            <p className="lede">{rotulosCopy.lede}</p>
            <p className="rotulos-howto">{rotulosCopy.howto}</p>
          </div>
          <div className="rotulos-keys">
            {LABEL_RUBRIC.map((row, index) => (
              <button
                key={row.value}
                className="btn"
                type="button"
                disabled={pending}
                aria-pressed={view.existingLabel === row.value}
                onClick={() => void label(row.value)}
              >
                <span className="rotulos-choice-label">
                  <kbd>{index + 1}</kbd>
                  {row.label}
                </span>
                <span className="rotulos-choice-hint">{rotulosCopy.hints[row.value]}</span>
              </button>
            ))}
          </div>
          <label className="field field-grow rotulos-notes">
            <span>{rotulosCopy.notes}</span>
            <input
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              maxLength={400}
              autoComplete="off"
              disabled={pending}
            />
          </label>
          <div className="actions rotulos-nav">
            <button
              className="btn-ghost"
              type="button"
              disabled={pending || !canSkip}
              onClick={() => void goTo(view.position + 1)}
            >
              {rotulosCopy.skip}
            </button>
            <button
              className="btn-ghost"
              type="button"
              disabled={pending || !canBack}
              onClick={() => void goTo(view.done ? view.total : view.position - 1)}
            >
              {rotulosCopy.back}
            </button>
          </div>
        </article>
      ) : (
        <article className="rotulos-card">
          <h1>{rotulosCopy.title}</h1>
          <p className="lede">{view.total === 0 ? rotulosCopy.empty : rotulosCopy.done}</p>
          {canBack ? (
            <div className="actions rotulos-nav">
              <button
                className="btn-ghost"
                type="button"
                disabled={pending}
                onClick={() => void goTo(view.total)}
              >
                {rotulosCopy.back}
              </button>
            </div>
          ) : null}
        </article>
      )}
    </div>
  )
}
