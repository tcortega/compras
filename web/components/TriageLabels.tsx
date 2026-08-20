import { LABEL_RUBRIC, triageCopy, type FlagRecord } from '@/lib/flags'

export function TriageLabels({ flag }: { flag: FlagRecord }) {
  return (
    <section className="section" aria-labelledby="rotulos-triagem">
      <h2 id="rotulos-triagem">{triageCopy.labels}</h2>
      <p className="lede">{triageCopy.precision}</p>
      <form className="triage-label-form" action="/interno/triagem/rotulo" method="post">
        <input type="hidden" name="id" value={flag.id} />
        <input type="hidden" name="itemId" value={flag.itemId} />
        <input type="hidden" name="kind" value={flag.kind} />
        <input type="hidden" name="evidence" value={flag.sourceUrl} />
        <label className="field field-grow">
          <span>{triageCopy.notes}</span>
          <input name="notes" maxLength={400} autoComplete="off" />
        </label>
        <div className="actions">
          {LABEL_RUBRIC.map((row) => (
            <button key={row.value} className="btn-ghost" type="submit" name="label" value={row.value}>
              {row.label}
            </button>
          ))}
        </div>
      </form>
    </section>
  )
}
