import { DataTable } from '@/components/DataTable'
import { ListFilters } from '@/components/ListFilters'
import { Pager } from '@/components/Pager'
import { SliceShell } from '@/components/SliceShell'
import { api } from '@/lib/api'
import { pageRequestFromSearch } from '@/lib/paging'
import { routes } from '@/lib/routes'
import { orgaoColumns } from '@/lib/tables'
import type { Metadata } from 'next'

export const metadata: Metadata = { title: 'Órgãos' }

type Search = Record<string, string | string[] | undefined>

export default async function OrgaosPage({ searchParams }: { searchParams: Promise<Search> }) {
  const req = pageRequestFromSearch(await searchParams)
  const page = await api.listOrgaos(req)

  return (
    <SliceShell coverage={page.coverage} current={routes.orgaos}>
      <p className="kicker">Coleção</p>
      <h1>Órgãos</h1>
      <p className="lede">Compradores do recorte publicado. Atribuição institucional, sem classificação de órgãos ou fornecedores.</p>
      <ListFilters
        action={routes.orgaos}
        q={req.q}
        extra={
          <>
            <label className="field field-uf">
              <span>UF</span>
              <input name="uf" defaultValue={req.uf ?? ''} maxLength={2} autoCapitalize="characters" />
            </label>
            <label className="field field-ibge">
              <span>IBGE</span>
              <input
                name="municipioIbge"
                defaultValue={req.municipioIbge ?? ''}
                inputMode="numeric"
                maxLength={7}
                placeholder="3303302"
              />
            </label>
            <label className="field">
              <span>Esfera</span>
              <select name="esfera" defaultValue={req.esfera ?? ''}>
                <option value="">Todas</option>
                <option value="federal">Federal</option>
                <option value="estadual">Estadual</option>
                <option value="municipal">Municipal</option>
              </select>
            </label>
          </>
        }
      />
      <DataTable
        rows={page.items}
        columns={orgaoColumns}
        coverage={page.coverage}
        footer={<Pager base={routes.orgaos} req={req} total={page.total} />}
      />
    </SliceShell>
  )
}
