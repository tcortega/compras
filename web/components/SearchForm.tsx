import { copy } from '@/lib/copy'
import { routes } from '@/lib/routes'

export function SearchForm({
  defaultValue = '',
  compact = false,
}: {
  defaultValue?: string
  compact?: boolean
}) {
  return (
    <form className="search" action={routes.busca} method="get" role="search">
      <label className="visually-hidden" htmlFor={compact ? 'q-list' : 'q-home'}>
        {copy.searchPlaceholder}
      </label>
      <input
        id={compact ? 'q-list' : 'q-home'}
        type="search"
        name="q"
        defaultValue={defaultValue}
        placeholder={copy.searchPlaceholder}
        autoComplete="off"
        enterKeyHint="search"
      />
      <button type="submit">{copy.searchSubmit}</button>
    </form>
  )
}
