import { Shell } from '@/components/Shell'
import { stubSliceCoverage } from '@/lib/api'
import { METHOD_VERSION } from '@/lib/copy'
import { routes } from '@/lib/routes'
import type { Metadata } from 'next'

export const metadata: Metadata = { title: 'Metodologia' }

export default function MetodologiaPage() {
  return (
    <Shell coverage={stubSliceCoverage}>
      <p className="kicker">Versão {METHOD_VERSION}</p>
      <h1>Metodologia do explorador</h1>
      <div className="prose">
        <p>Fase 2: busca, listagem e ficha. Sem pontuação, sem ranking e sem publicação de flags.</p>
        <p>As rotas lidas são GET /api/orgaos, /api/fornecedores, /api/contratacoes e /api/items, com detalhe por id.</p>
        <p>Listas usam PageRequest com skip e take no servidor. Não há ordenação por score.</p>
        <p>Páginas de entidade são geradas com ISR (revalidate 3600) para caber atrás de CDN.</p>
        <p>CPF chega mascarado da origem e não é exibido em campo próprio.</p>
        <p>O texto público publica número, fonte e snapshot. Não usa rótulo de veredito.</p>
        <p>
          A cobertura do recorte está em <a href={routes.cobertura}>Cobertura</a>.
        </p>
      </div>
    </Shell>
  )
}
