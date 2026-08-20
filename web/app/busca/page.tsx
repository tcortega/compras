import { DataTable } from '@/components/DataTable'
import { SearchForm } from '@/components/SearchForm'
import { Shell } from '@/components/Shell'
import { api } from '@/lib/api'
import { pageRequestFromSearch } from '@/lib/paging'
import { routes } from '@/lib/routes'
import { contratacaoColumns, fornecedorColumns, itemColumns, orgaoColumns } from '@/lib/tables'
import type { Metadata } from 'next'

export const metadata: Metadata = { title: 'Busca' }

type Search = Record<string, string | string[] | undefined>

export default async function BuscaPage({ searchParams }: { searchParams: Promise<Search> }) {
  const sp = await searchParams
  const base = pageRequestFromSearch(sp)
  const req = { ...base, skip: 0, take: 5 }
  const q = req.q ?? ''

  const [orgaos, fornecedores, contratacoes, items] = q
    ? await Promise.all([
        api.listOrgaos(req),
        api.listFornecedores(req),
        api.listContratacoes(req),
        api.listItems(req),
      ])
    : await Promise.all([
        api.listOrgaos({ skip: 0, take: 1 }),
        api.listFornecedores({ skip: 0, take: 1 }),
        api.listContratacoes({ skip: 0, take: 1 }),
        api.listItems({ skip: 0, take: 1 }),
      ])

  return (
    <Shell coverage={items.coverage}>
      <p className="kicker">Busca</p>
      <h1>{q ? `Resultados para “${q}”` : 'Buscar no recorte'}</h1>
      <p className="lede">
        A busca consulta as quatro coleções publicadas. Não há índice de ranking nem pontuação.
      </p>
      <SearchForm defaultValue={q} />

      {!q ? (
        <p className="muted">Informe um termo. A consulta usa skip/take em cada endpoint.</p>
      ) : (
        <>
          <section className="group">
            <div className="section-head">
              <h2>Órgãos</h2>
              <a href={`${routes.orgaos}?q=${encodeURIComponent(q)}`}>Ver todos</a>
            </div>
            <DataTable rows={orgaos.items} columns={orgaoColumns} coverage={orgaos.coverage} />
          </section>
          <section className="group">
            <div className="section-head">
              <h2>Fornecedores</h2>
              <a href={`${routes.fornecedores}?q=${encodeURIComponent(q)}`}>Ver todos</a>
            </div>
            <DataTable rows={fornecedores.items} columns={fornecedorColumns} coverage={fornecedores.coverage} />
          </section>
          <section className="group">
            <div className="section-head">
              <h2>Contratações</h2>
              <a href={`${routes.contratacoes}?q=${encodeURIComponent(q)}`}>Ver todos</a>
            </div>
            <DataTable rows={contratacoes.items} columns={contratacaoColumns} coverage={contratacoes.coverage} />
          </section>
          <section className="group">
            <div className="section-head">
              <h2>Itens</h2>
              <a href={`${routes.itens}?q=${encodeURIComponent(q)}`}>Ver todos</a>
            </div>
            <DataTable rows={items.items} columns={itemColumns} coverage={items.coverage} />
          </section>
        </>
      )}
    </Shell>
  )
}
