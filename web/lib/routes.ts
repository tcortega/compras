export const routes = {
  home: '/',
  busca: '/busca',
  orgaos: '/orgaos',
  orgao: (id: string) => `/orgaos/${id}` as const,
  fornecedores: '/fornecedores',
  fornecedor: (id: string) => `/fornecedores/${id}` as const,
  contratacoes: '/contratacoes',
  contratacao: (id: string) => `/contratacoes/${id}` as const,
  itens: '/itens',
  item: (id: string) => `/itens/${id}` as const,
  cobertura: '/cobertura',
  metodologia: '/metodologia',
  triagem: '/interno/triagem',
  triagemItem: (id: string) => `/interno/triagem/${id}` as const,
} as const

export const navPrimary = [
  { href: routes.orgaos, label: 'Órgãos' },
  { href: routes.fornecedores, label: 'Fornecedores' },
  { href: routes.contratacoes, label: 'Contratações' },
  { href: routes.itens, label: 'Itens' },
] as const
