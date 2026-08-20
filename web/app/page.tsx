import { CoverageChip } from '@/components/CoverageChip'
import { SearchForm } from '@/components/SearchForm'
import { Shell } from '@/components/Shell'
import { api } from '@/lib/api'
import { copy, SLICE_LABEL, SLICE_YEAR } from '@/lib/copy'
import { formatNumber } from '@/lib/format'
import { routes } from '@/lib/routes'

export const dynamic = 'force-dynamic'

export default async function HomePage() {
  const [orgaos, fornecedores, contratacoes, items] = await Promise.all([
    api.listOrgaos({ skip: 0, take: 1 }),
    api.listFornecedores({ skip: 0, take: 1 }),
    api.listContratacoes({ skip: 0, take: 1 }),
    api.listItems({ skip: 0, take: 1 }),
  ])

  const cards = [
    { href: routes.orgaos, kicker: 'Órgãos', total: orgaos.total, coverage: orgaos.coverage },
    { href: routes.fornecedores, kicker: 'Fornecedores', total: fornecedores.total, coverage: fornecedores.coverage },
    { href: routes.contratacoes, kicker: 'Contratações', total: contratacoes.total, coverage: contratacoes.coverage },
    { href: routes.itens, kicker: 'Itens', total: items.total, coverage: items.coverage },
  ]

  return (
    <Shell coverage={items.coverage} current={routes.home}>
      <section className="hero">
        <p className="kicker">Recorte publicado · {SLICE_YEAR}</p>
        <h1>O que foi comprado com dinheiro público.</h1>
        <p className="lede">
          Recorte publicado: {SLICE_LABEL}.
          Busca, listagem e ficha de órgão, fornecedor, contratação e item.
          Cada agregado traz o denominador da cobertura.
          Sem classificação de órgãos ou fornecedores, sem pontuação e sem juízo.
        </p>
        <SearchForm />
        <div className="notice">
          <p>{copy.coverageExempt}</p>
        </div>
      </section>
      <section className="index-grid" aria-label="Totais do recorte">
        {cards.map((card) => (
          <a key={card.href} className="index-card" href={card.href}>
            <p className="kicker">{card.kicker}</p>
            <strong>{formatNumber(card.total)}</strong>
            <CoverageChip coverage={card.coverage} />
          </a>
        ))}
      </section>
    </Shell>
  )
}
