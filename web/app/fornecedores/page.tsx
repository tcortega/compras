import { DataTable } from '@/components/DataTable'
import { ListFilters } from '@/components/ListFilters'
import { Pager } from '@/components/Pager'
import { SliceShell } from '@/components/SliceShell'
import { api } from '@/lib/api'
import { pageRequestFromSearch } from '@/lib/paging'
import { routes } from '@/lib/routes'
import { fornecedorColumns } from '@/lib/tables'
import type { Metadata } from 'next'

export const metadata: Metadata = { title: 'Fornecedores' }

type Search = Record<string, string | string[] | undefined>

export default async function FornecedoresPage({ searchParams }: { searchParams: Promise<Search> }) {
  const req = pageRequestFromSearch(await searchParams)
  const page = await api.listFornecedores(req)

  return (
    <SliceShell coverage={page.coverage} current={routes.fornecedores}>
      <p className="kicker">Coleção</p>
      <h1>Fornecedores</h1>
      <p className="lede">Pessoas jurídicas que venderam no recorte. CPF não é publicado.</p>
      <ListFilters action={routes.fornecedores} q={req.q} />
      <DataTable
        rows={page.items}
        columns={fornecedorColumns}
        coverage={page.coverage}
        footer={<Pager base={routes.fornecedores} req={req} total={page.total} />}
      />
    </SliceShell>
  )
}
