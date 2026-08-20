# /web

Explorador cidadão do recorte de compras públicas.

Fase 2: busca, lista e ficha de órgãos, fornecedores, contratações e itens.
Sem pontuação, sem ranking e sem flags públicas.

Cada agregado na tela mostra o denominador da cobertura (`n`, UF, trimestre).
A interface afirma cobertura incompleta e não afirma censo nacional.

## API

O cliente tipado fala só com o contrato de `docs/CONTRACT.md`:

- `GET /api/orgaos` e `GET /api/orgaos/{id}`
- `GET /api/fornecedores` e `GET /api/fornecedores/{id}`
- `GET /api/contratacoes` e `GET /api/contratacoes/{id}`
- `GET /api/items` e `GET /api/items/{id}`

Listas usam `PageRequest` com `skip` e `take`.
Páginas de entidade usam ISR (`revalidate = 3600`) e `generateStaticParams`.

## Rodar

```bash
cp .env.example .env.local
npm install
npm run dev
```

`API_BASE_URL=stub` (padrão) usa o recorte em processo: Volta Redonda, RJ, 2024.
Aponte `API_BASE_URL` para a API C# quando ela existir, por exemplo `http://localhost:5080`.

```bash
npm run build
npm start
npm run e2e
```

O E2E cobre busca e drill-down contra o stub.
Não há suíte de unit tests.
