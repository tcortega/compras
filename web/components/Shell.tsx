import { CoverageBar } from '@/components/CoverageBar'
import { copy, SITE_NAME, SITE_TAG, SLICE_LABEL } from '@/lib/copy'
import { navPrimary, routes } from '@/lib/routes'
import type { Coverage } from '@/lib/types'
import type { ReactNode } from 'react'

export function Shell({
  children,
  coverage,
  current,
}: {
  children: ReactNode
  coverage: Coverage
  current?: string
}) {
  return (
    <>
      <a className="skip" href="#conteudo">
        Ir ao conteúdo
      </a>
      <header className="masthead">
        <div className="wrap masthead-inner">
          <a className="brand" href={routes.home}>
            <span className="brand-kicker">{SLICE_LABEL}</span>
            <span className="brand-name">{SITE_NAME}</span>
            <span className="brand-tag">{SITE_TAG}</span>
          </a>
          <nav className="nav" aria-label="Seções">
            {navPrimary.map((item) => (
              <a
                key={item.href}
                href={item.href}
                aria-current={current === item.href ? 'page' : undefined}
              >
                {item.label}
              </a>
            ))}
          </nav>
        </div>
      </header>
      <CoverageBar coverage={coverage} />
      <main id="conteudo" className="page">
        <div className="wrap">{children}</div>
      </main>
      <footer className="footer">
        <div className="wrap footer-inner">
          <p>
            {copy.coverageIncomplete} Recorte publicado: {SLICE_LABEL}.
          </p>
          <nav aria-label="Rodapé">
            <a href={routes.cobertura}>Cobertura</a>
            <a href={routes.metodologia}>Metodologia</a>
          </nav>
        </div>
      </footer>
    </>
  )
}
