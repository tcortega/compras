import { rangeLabel } from '@/lib/paging'
import type { PageRequest } from '@/lib/types'

function hrefFor(
  base: string,
  req: PageRequest,
  skip: number,
  extra?: Record<string, string | undefined>,
): string {
  const params = new URLSearchParams()
  if (req.q) params.set('q', req.q)
  if (req.uf) params.set('uf', req.uf)
  if (req.municipioIbge) params.set('municipioIbge', req.municipioIbge)
  if (req.esfera) params.set('esfera', req.esfera)
  if (req.orgaoId) params.set('orgaoId', req.orgaoId)
  if (req.fornecedorId) params.set('fornecedorId', req.fornecedorId)
  if (req.contratacaoId) params.set('contratacaoId', req.contratacaoId)
  if (req.ano != null) params.set('ano', String(req.ano))
  if (req.quarter) params.set('quarter', req.quarter)
  if (req.take !== 20) params.set('take', String(req.take))
  if (skip > 0) params.set('skip', String(skip))
  if (extra) {
    for (const [key, value] of Object.entries(extra)) {
      if (value) params.set(key, value)
    }
  }
  const q = params.toString()
  return q ? `${base}?${q}` : base
}

export function Pager({
  base,
  req,
  total,
  extra,
}: {
  base: string
  req: PageRequest
  total: number
  extra?: Record<string, string | undefined>
}) {
  const prev = Math.max(0, req.skip - req.take)
  const next = req.skip + req.take
  const hasPrev = req.skip > 0
  const hasNext = next < total

  return (
    <nav className="pager" aria-label="Paginação">
      {hasPrev ? <a href={hrefFor(base, req, prev, extra)}>Anterior</a> : <span aria-disabled="true">Anterior</span>}
      <span>{rangeLabel(req.skip, req.take, total)}</span>
      {hasNext ? <a href={hrefFor(base, req, next, extra)}>Próxima</a> : <span aria-disabled="true">Próxima</span>}
    </nav>
  )
}
