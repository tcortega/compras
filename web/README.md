# /web

Explorador cidadão do recorte de compras públicas.

Fase 2: busca, lista e ficha de órgãos, fornecedores, contratações e itens.
Sem pontuação, sem classificação de órgãos ou fornecedores e sem alertas públicos.

Cada agregado na tela mostra o denominador da cobertura (`n`, UF, trimestre).
A interface afirma cobertura incompleta e não afirma censo nacional.

## API

O cliente tipado fala só com o contrato de `docs/CONTRACT.md`:

- `GET /api/orgaos` e `GET /api/orgaos/{id}`
- `GET /api/fornecedores` e `GET /api/fornecedores/{id}`
- `GET /api/contratacoes` e `GET /api/contratacoes/{id}`
- `GET /api/items` e `GET /api/items/{id}`

Listas usam `PageRequest` com `skip` e `take`.
Páginas de entidade renderizam sob demanda.
No compose isso lê a API C#.
Fora do compose, `API_BASE_URL=stub` lê o recorte em processo.

## Rodar

```bash
cp .env.example .env.local
npm install
npm run dev
```

`API_BASE_URL=stub` (padrão) usa o recorte em processo: Volta Redonda e Niterói (RJ), Bauru (SP), Caxias do Sul (RS), Joinville (SC), Uberlândia (MG), Londrina (PR), Feira de Santana (BA), Caruaru (PE), Anápolis (GO), Vila Velha (ES), Campina Grande (PB), Caucaia (CE), Imperatriz (MA), Arapiraca (AL), Dourados (MS), Marabá (PA), Várzea Grande (MT), Ji-Paraná (RO), Parnamirim (RN), Cruzeiro do Sul (AC), Santana (AP), Rorainópolis (RR), Maringá (PR), Taubaté (SP), Cascavel (PR), Juiz de Fora (MG), Foz do Iguaçu (PR), Santa Maria (RS), Montes Claros (MG), Governador Valadares (MG), Canoas (RS), Lages (SC), Santarém (PA) e Rio Verde (GO), 2024.
O compose em `/infra` aponta `API_BASE_URL` para `http://api:5080` e publica o explorador em http://127.0.0.1:3100.
Fora do compose, aponte `API_BASE_URL` para a API C#, por exemplo `http://127.0.0.1:5080`.
Se `API_BASE_URL` aponta para a API, o cliente HTTP é obrigatório e o stub não pode responder.

```bash
npm run build
npm start
npm run e2e
```

`npm run e2e` cobre busca e drill-down contra o stub.
`npm run e2e:compose` aponta o mesmo spec para o explorador do compose em :3100.
O spec não assume campos só do stub. CI do compose também roda esse Playwright.
Não há suíte de unit tests.
