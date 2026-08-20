'use client'

import { Shell } from '@/components/Shell'
import { copy } from '@/lib/copy'
import { routes } from '@/lib/routes'

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <Shell>
      <p className="kicker">Erro</p>
      <h1>{copy.loadError}</h1>
      <p className="lede">A origem não respondeu a este pedido. Tente de novo ou volte ao recorte inicial.</p>
      <p className="actions">
        <button className="btn" type="button" onClick={reset}>
          Tentar de novo
        </button>
        <a className="btn-ghost" href={routes.home}>
          Início
        </a>
      </p>
    </Shell>
  )
}
