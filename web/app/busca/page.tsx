import { DataTable } from '@/components/DataTable'
import { SearchForm } from '@/components/SearchForm'
import { SliceShell } from '@/components/SliceShell'
import { api } from '@/lib/api'
import { pageRequestFromSearch } from '@/lib/paging'
import { routes } from '@/lib/routes'
import { fornecedorColumns, itemColumns, orgaoColumns } from '@/lib/tables'
import type { SearchSource } from '@/lib/types'
import type { Metadata } from 'next'

export const metadata: Metadata = { title: 'Busca' }

type Search = Record<string, string | string[] | undefined>

function sourceLine(source: SearchSource): string {
  if (source === 'meilisearch') return 'Índice Meilisearch. Texto factual do recorte, sem pontuação.'
  if (source === 'unavailable') return 'Índice indisponível. Nenhum resultado inventado.'
  if (source === 'unset') return 'Índice não configurado. Nenhum resultado inventado.'
  return 'Filtro do recorte (warehouse). Sem pontuação.'
}

export default async function BuscaPage({ searchParams }: { searchParams: Promise<Search> }) {
  const sp = await searchParams
  const base = pageRequestFromSearch(sp)
  const req = { ...base, skip: 0, take: 5 }
  const q = req.q ?? ''
  const found = await api.search({ ...req, q: q || undefined })

  return (
    <SliceShell coverage={found.coverage}>
      <p className="kicker">Busca</p>
      <h1>{q ? `Resultados para “${q}”` : 'Buscar no recorte'}</h1>
      <p className="lede">
        A busca consulta órgãos, fornecedores e itens. Não há classificação de órgãos ou fornecedores nem pontuação.
      </p>
      <SearchForm defaultValue={q} />
      <p className="muted">{sourceLine(found.source)}</p>

      {!q ? (
        <p className="muted">Informe um termo para consultar o índice deste recorte.</p>
      ) : (
        <>
          <section className="group">
            <div className="section-head">
              <h2>Órgãos</h2>
              <a href={`${routes.orgaos}?q=${encodeURIComponent(q)}`}>Ver todos</a>
            </div>
            <DataTable rows={found.orgaos.items} columns={orgaoColumns} coverage={found.orgaos.coverage} />
          </section>
          <section className="group">
            <div className="section-head">
              <h2>Fornecedores</h2>
              <a href={`${routes.fornecedores}?q=${encodeURIComponent(q)}`}>Ver todos</a>
            </div>
            <DataTable rows={found.fornecedores.items} columns={fornecedorColumns} coverage={found.fornecedores.coverage} />
          </section>
          <section className="group">
            <div className="section-head">
              <h2>Itens</h2>
              <a href={`${routes.itens}?q=${encodeURIComponent(q)}`}>Ver todos</a>
            </div>
            <DataTable rows={found.items.items} columns={itemColumns} coverage={found.items.coverage} />
          </section>
        </>
      )}
    </SliceShell>
  )
}
