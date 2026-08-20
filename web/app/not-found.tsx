import { Shell } from '@/components/Shell'
import { copy } from '@/lib/copy'
import { routes } from '@/lib/routes'

export default function NotFound() {
  return (
    <Shell>
      <p className="kicker">404</p>
      <h1>{copy.notFound}</h1>
      <p className="lede">O identificador não existe neste recorte publicado.</p>
      <p>
        <a href={routes.home}>Voltar ao início</a>
      </p>
    </Shell>
  )
}
