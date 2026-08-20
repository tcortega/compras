import { SliceShell } from '@/components/SliceShell'
import { loadSliceCoverage } from '@/lib/api'
import { copy } from '@/lib/copy'
import { routes } from '@/lib/routes'

export const dynamic = 'force-dynamic'

export default async function NotFound() {
  const coverage = await loadSliceCoverage()
  return (
    <SliceShell coverage={coverage}>
      <p className="kicker">404</p>
      <h1>{copy.notFound}</h1>
      <p className="lede">O identificador não existe neste recorte publicado.</p>
      <p className="actions">
        <a className="btn" href={routes.home}>
          Voltar ao início
        </a>
      </p>
    </SliceShell>
  )
}
