import type { ReactNode } from 'react'

export function EntityHeader({
  kicker,
  title,
  lede,
  children,
}: {
  kicker: string
  title: string
  lede?: string
  children?: ReactNode
}) {
  return (
    <header>
      <p className="kicker">{kicker}</p>
      <h1>{title}</h1>
      {lede ? <p className="lede">{lede}</p> : null}
      {children}
    </header>
  )
}
