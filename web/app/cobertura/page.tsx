import { Shell } from '@/components/Shell'
import { loadSliceCoverage } from '@/lib/api'
import { SLICE_LABEL, SLICE_MUNICIPIOS, copy } from '@/lib/copy'
import { coverageText } from '@/lib/coverage'
import type { Metadata } from 'next'

export const dynamic = 'force-dynamic'
export const metadata: Metadata = { title: 'Cobertura' }

export default async function CoberturaPage() {
  const coverage = await loadSliceCoverage()
  return (
    <Shell coverage={coverage}>
      <p className="kicker">Denominador</p>
      <h1>Cobertura incompleta</h1>
      <div className="prose">
        <p>Este recorte publicado é {SLICE_LABEL}.</p>
        <p>
          Municípios ingeridos:{' '}
          {SLICE_MUNICIPIOS.map((m) => `${m.nome} (${m.uf}, IBGE ${m.ibge})`).join('; ')}.
        </p>
        <p>Denominador atual: {coverageText(coverage)}.</p>
        <p>Quando o recorte mistura UF, o agregado deixa UF vazia. Isso não é um total nacional.</p>
        <p>{copy.coverageIncomplete}</p>
        <p>{copy.coverageExempt}</p>
        <p>{copy.coverageQuality}</p>
        <p>Lei 8.666/93 foi revogada em 30 de dezembro de 2023. 2024 é o primeiro ano de item municipal centralizado.</p>
        <p>Cobertura municipal nacional não é alcançável antes de cerca de 2027-2028. Nenhum agregado nesta interface afirma o contrário.</p>
        <p>Todo total na tela mostra n, UF, trimestre e a versão da metodologia. Se o trimestre varia no recorte, o chip diz vários trimestres.</p>
      </div>
    </Shell>
  )
}
