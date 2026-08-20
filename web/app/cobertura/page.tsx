import { Shell } from '@/components/Shell'
import { loadCobertura } from '@/lib/api'
import { copy } from '@/lib/copy'
import { coverageText } from '@/lib/coverage'
import {
  formatDate,
  formatLandingSource,
  formatNumber,
  formatPercent,
} from '@/lib/format'
import type { Metadata } from 'next'

export const dynamic = 'force-dynamic'
export const metadata: Metadata = { title: 'Cobertura' }

export default async function CoberturaPage() {
  const payload = await loadCobertura()
  const yearsLabel = payload.years.length ? payload.years.join(', ') : copy.noValue
  return (
    <Shell coverage={payload.coverage}>
      <p className="kicker">Denominador</p>
      <h1>Cobertura incompleta</h1>
      <p className="lede">
        Recorte ingerido no warehouse, não um censo nacional.
        Os números abaixo vêm do recorte publicado, município a município.
      </p>
      <div className="notice">
        <p>{copy.coverageIncomplete}</p>
        <p>{copy.coverageExempt}</p>
        <p>{copy.coverageQuality}</p>
      </div>
      <section className="stats" aria-label="Números do recorte">
        <div className="stat">
          <p className="kicker">Municípios</p>
          <strong>{formatNumber(payload.municipios.n)}</strong>
        </div>
        <div className="stat">
          <p className="kicker">Anos</p>
          <strong>{yearsLabel}</strong>
        </div>
        <div className="stat">
          <p className="kicker">Contratações</p>
          <strong>{formatNumber(payload.rows.compras)}</strong>
        </div>
        <div className="stat">
          <p className="kicker">Itens</p>
          <strong>{formatNumber(payload.rows.items)}</strong>
        </div>
      </section>
      <section className="section">
        <h2>Join CATMAT exato</h2>
        <p className="catmat-live">
          Join exato ao vivo: {formatPercent(payload.catmatCoveragePercent)} ({formatNumber(payload.nCoded)} de{' '}
          {formatNumber(payload.nItems)} itens).
        </p>
        <p className="muted">
          Inteiro exato de item.catmat ou item.catser contra o catálogo ingerido.
          Sem kNN e sem texto aproximado.
        </p>
        <p className="muted">
          A linha de base rotulada da Fase 0 em Volta Redonda 2024 é 81,75% no join exato daquele recorte
          rotulado.
          Esse número não é o percentual ao vivo deste recorte.
        </p>
      </section>
      <section className="section">
        <div className="section-head">
          <h2>Municípios ingeridos</h2>
          <span className="muted">{formatNumber(payload.municipios.n)} no warehouse</span>
        </div>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Município</th>
                <th>UF</th>
                <th className="mono">IBGE</th>
              </tr>
            </thead>
            <tbody>
              {payload.municipios.items.map((m) => (
                <tr key={m.ibge}>
                  <td>{m.nome}</td>
                  <td>{m.uf}</td>
                  <td className="mono">{m.ibge}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="section">
        <h2>Por ano</h2>
        <ul>
          {payload.rows.perYear.map((row) => (
            <li key={row.year}>
              {row.year}: {formatNumber(row.compras)} contratações, {formatNumber(row.items)} itens.
            </li>
          ))}
        </ul>
      </section>
      <section className="section">
        <div className="section-head">
          <h2>Fontes</h2>
          <span className="muted">Última ingestão no landing, sem data inventada</span>
        </div>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Fonte</th>
                <th className="num">Linhas</th>
                <th>Última ingestão</th>
              </tr>
            </thead>
            <tbody>
              {payload.sources.map((source) => (
                <tr key={source.name} className="source-row">
                  <td>
                    {formatLandingSource(source.name)}{' '}
                    <span className="muted mono">{source.name}</span>
                  </td>
                  <td className="num">{formatNumber(source.n)}</td>
                  <td>{source.lastUpdate ? formatDate(source.lastUpdate) : 'sem ingestão'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <div className="prose">
        <p>Denominador atual: {coverageText(payload.coverage)}.</p>
        <p>Quando o recorte mistura UF, o agregado deixa UF vazia. Isso não é um total nacional.</p>
        <p>Homologado não entra no total de órgão nem de fornecedor.</p>
        <p>Lei 8.666/93 foi revogada em 30 de dezembro de 2023. 2024 é o primeiro ano de item municipal centralizado.</p>
        <p>Cobertura municipal nacional não é alcançável antes de cerca de 2027-2028. Nenhum agregado nesta interface afirma o contrário.</p>
        <p>Todo total na tela mostra n, UF, trimestre e a versão da metodologia. Se o trimestre varia no recorte, o chip diz vários trimestres.</p>
      </div>
    </Shell>
  )
}
