import { DataTable } from '@/components/DataTable'
import { ListFilters } from '@/components/ListFilters'
import { Pager } from '@/components/Pager'
import { Shell } from '@/components/Shell'
import { api } from '@/lib/api'
import { pageRequestFromSearch } from '@/lib/paging'
import { routes } from '@/lib/routes'
import { contratacaoColumns } from '@/lib/tables'
import type { Metadata } from 'next'

export const metadata: Metadata = { title: 'Contratações' }

type Search = Record<string, string | string[] | undefined>

export default async function ContratacoesPage({ searchParams }: { searchParams: Promise<Search> }) {
  const req = pageRequestFromSearch(await searchParams)
  const page = await api.listContratacoes(req)

  return (
    <Shell coverage={page.coverage} current={routes.contratacoes}>
      <p className="kicker">Coleção</p>
      <h1>Contratações</h1>
      <p className="lede">Procedimentos publicados no recorte, com fonte e snapshot.</p>
      <ListFilters
        action={routes.contratacoes}
        q={req.q}
        extra={
          <>
            <label className="field">
              <span>Ano</span>
              <input name="ano" inputMode="numeric" defaultValue={req.ano ? String(req.ano) : ''} />
            </label>
            {req.orgaoId ? <input type="hidden" name="orgaoId" value={req.orgaoId} /> : null}
          </>
        }
      />
      <DataTable
        rows={page.items}
        columns={contratacaoColumns}
        coverage={page.coverage}
        footer={<Pager base={routes.contratacoes} req={req} total={page.total} />}
      />
    </Shell>
  )
}
