import { Shell } from '@/components/Shell'
import { loadSliceCoverage } from '@/lib/api'
import { routes } from '@/lib/routes'
import type { Metadata } from 'next'

export const dynamic = 'force-dynamic'
export const metadata: Metadata = { title: 'Metodologia' }

export default async function MetodologiaPage() {
  const coverage = await loadSliceCoverage()
  return (
    <Shell coverage={coverage}>
      <p className="kicker">Versão {coverage.methodologyVersion}</p>
      <h1>Metodologia do explorador</h1>
      <div className="prose">
        <p>Fase 2: busca, listagem e ficha. Sem pontuação, sem classificação de órgãos ou fornecedores e sem alertas públicos.</p>
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
