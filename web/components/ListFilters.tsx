import type { ReactNode } from 'react'

export function ListFilters({
  action,
  q,
  extra,
}: {
  action: string
  q?: string
  extra?: ReactNode
}) {
  return (
    <form className="filters" action={action} method="get">
      <label className="field field-grow">
        <span>Busca</span>
        <input type="search" name="q" defaultValue={q ?? ''} autoComplete="off" />
      </label>
      {extra}
      <button className="btn-ghost" type="submit">
        Filtrar
      </button>
    </form>
  )
}
