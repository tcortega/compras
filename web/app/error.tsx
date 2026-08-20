'use client'

import { copy } from '@/lib/copy'
import { routes } from '@/lib/routes'

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="page">
      <div className="wrap">
        <p className="kicker">Erro</p>
        <h1>{copy.loadError}</h1>
        <p className="lede">A origem não respondeu a este pedido. Tente de novo ou volte ao recorte inicial.</p>
        <p>
          <button className="btn" type="button" onClick={reset}>
            Tentar de novo
          </button>
        </p>
        <p>
          <a href={routes.home}>Início</a>
        </p>
      </div>
    </main>
  )
}
