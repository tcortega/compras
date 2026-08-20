import { Shell } from '@/components/Shell'
import { loadSliceCoverage } from '@/lib/api'
import { copy } from '@/lib/copy'
import { explorerDynamic, explorerRevalidate } from '@/lib/rendering'
import { routes } from '@/lib/routes'

export const dynamic = explorerDynamic
export const revalidate = explorerRevalidate

export default async function NotFound() {
  const coverage = await loadSliceCoverage()
  return (
    <Shell coverage={coverage}>
      <p className="kicker">404</p>
      <h1>{copy.notFound}</h1>
      <p className="lede">O identificador não existe neste recorte publicado.</p>
      <p>
        <a href={routes.home}>Voltar ao início</a>
      </p>
    </Shell>
  )
}
