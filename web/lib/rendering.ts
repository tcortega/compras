export const skipStaticParams = process.env.SKIP_STATIC_PARAMS === '1'

export const explorerDynamic = skipStaticParams ? 'force-dynamic' : 'auto'

export const explorerRevalidate = skipStaticParams ? 0 : 3600

export async function staticEntityIds(
  list: () => Promise<{ items: Array<{ id: string }> }>,
): Promise<Array<{ id: string }>> {
  if (skipStaticParams || !usesStubAtBuild()) return []
  const page = await list()
  return page.items.map((row) => ({ id: row.id }))
}

function usesStubAtBuild(): boolean {
  const base = (process.env.API_BASE_URL ?? 'stub').trim()
  return base === '' || base === 'stub'
}
