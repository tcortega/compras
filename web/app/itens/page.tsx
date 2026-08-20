import { DataTable } from '@/components/DataTable'
import { ListFilters } from '@/components/ListFilters'
import { Pager } from '@/components/Pager'
import { Shell } from '@/components/Shell'
import { api } from '@/lib/api'
import { pageRequestFromSearch } from '@/lib/paging'
import { routes } from '@/lib/routes'
import { itemColumns } from '@/lib/tables'
import type { Metadata } from 'next'

export const metadata: Metadata = { title: 'Itens' }

type Search = Record<string, string | string[] | undefined>

export default async function ItensPage({ searchParams }: { searchParams: Promise<Search> }) {
  const req = pageRequestFromSearch(await searchParams)
  const page = await api.listItems(req)

  return (
    <Shell coverage={page.coverage} current={routes.itens}>
      <p className="kicker">Coleção</p>
      <h1>Itens</h1>
      <p className="lede">Linha de compra com unidade, valor e CATMAT quando existir.</p>
      <ListFilters
        action={routes.itens}
        q={req.q}
        extra={
          <>
            <label className="field field-uf">
              <span>UF</span>
              <input name="uf" defaultValue={req.uf ?? ''} maxLength={2} autoCapitalize="characters" />
            </label>
            <label className="field field-quarter">
              <span>Trimestre</span>
              <input name="quarter" defaultValue={req.quarter ?? ''} placeholder="2024-Q2" />
            </label>
            {req.orgaoId ? <input type="hidden" name="orgaoId" value={req.orgaoId} /> : null}
            {req.fornecedorId ? <input type="hidden" name="fornecedorId" value={req.fornecedorId} /> : null}
            {req.contratacaoId ? <input type="hidden" name="contratacaoId" value={req.contratacaoId} /> : null}
          </>
        }
      />
      <DataTable
        rows={page.items}
        columns={itemColumns}
        coverage={page.coverage}
        footer={<Pager base={routes.itens} req={req} total={page.total} />}
      />
    </Shell>
  )
}
