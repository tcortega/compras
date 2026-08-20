import { FLAG_STATES, STATE_LABEL } from '@/lib/flags'
import { routes } from '@/lib/routes'

export function TriageFilters({ kind, state }: { kind?: string; state?: string }) {
  return (
    <form className="filters" action={routes.triagem} method="get">
      <label className="field field-grow">
        <span>Tipo</span>
        <input name="kind" defaultValue={kind ?? ''} autoComplete="off" />
      </label>
      <label className="field">
        <span>Estado</span>
        <select name="state" defaultValue={state ?? ''}>
          <option value="">Todos</option>
          {FLAG_STATES.map((value) => (
            <option key={value} value={value}>
              {STATE_LABEL[value]}
            </option>
          ))}
        </select>
      </label>
      <button className="btn-ghost" type="submit">
        Filtrar
      </button>
    </form>
  )
}
