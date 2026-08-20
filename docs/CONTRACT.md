# Warehouse and API contract

Python never calls C#.
C# never runs a detector.
Postgres holds canonical entities.
ClickHouse holds analytical item facts.
The explorer may start on Postgres.

## Identity

Phase 0 precision slice: Volta Redonda, RJ, IBGE 3306305, year 2024.
The published explorer slice also lands Niterói, RJ, IBGE 3303302, Bauru, SP, IBGE 3506003, Caxias do Sul, RS, IBGE 4305108, Joinville, SC, IBGE 4209102, Uberlândia, MG, IBGE 3170206, Londrina, PR, IBGE 4113700, Feira de Santana, BA, IBGE 2910800, Caruaru, PE, IBGE 2604106, Anápolis, GO, IBGE 5201108, Vila Velha, ES, IBGE 3205200, Campina Grande, PB, IBGE 2504009, Caucaia, CE, IBGE 2303709, Imperatriz, MA, IBGE 2105302, Arapiraca, AL, IBGE 2700300, Dourados, MS, IBGE 5003702, and Marabá, PA, IBGE 1504208, year 2024, from the same Compras.gov / PNCP 2024 bulk.
That published set does not limit the schema.
A mixed-UF aggregate leaves `uf` empty.
It is not a national total.

CPF is masked at ingest as `***.XXX.XXX-**`.
Never store raw CPF.

Every aggregate returned by the API carries a coverage denominator: `n`, `uf`, `quarter`, `methodologyVersion`.
Never imply national completeness.

## Postgres entities

Closed sets are enums stored as text.

### orgao

`id` uuid.
`cnpj` text unique.
`razaoSocial` text.
`esfera` federal | estadual | municipal.
`poder` text.
`uf` text.
`municipioIbge` text.
`municipioNome` text.
`suspended` bool default false.
`createdAt` / `updatedAt` Instant.

### fornecedor

`id` uuid.
`cnpj` text unique.
`razaoSocial` text.
`openedOn` LocalDate nullable.
`cnae` text nullable.
`suspended` bool default false.
`createdAt` / `updatedAt` Instant.

### contratacao

`id` uuid.
`pncpId` text unique.
`orgaoId` uuid.
`modalidade` text.
`objeto` text.
`ano` int.
`valorHomologado` numeric nullable.
`publicadoEm` Instant nullable.
`source` text.
`snapshotId` text.
`methodologyVersion` text.
`suspended` bool default false.
`createdAt` / `updatedAt` Instant.

### item

`id` uuid.
`contratacaoId` uuid.
`fornecedorId` uuid nullable.
`descricao` text.
`catmat` text nullable.
`catser` text nullable.
`quantidade` numeric.
`unidadeMedida` text.
`unidadeCanonica` text nullable.
Closed set from `normalize/compras_normalize/data/unidade_medida.csv`, or the explicit token `unknown` when the source unit does not match.
`valorUnitario` numeric nullable.
`valorTotal` numeric nullable.
`valorPorUnidadeCanonica` numeric nullable.
Price per canonical unit is `valorUnitario / to_base_factor`.
When unit price is missing it is `valorTotal / (quantidade * to_base_factor)`.
`to_base_factor` is how many canonical units sit in one source unit.
Unknown units stay `unknown` and leave `valorPorUnidadeCanonica` null.
Do not invent a unit or a comparable price.
`uf` text.
`quarter` text.
`snapshotId` text.
`methodologyVersion` text.
`suspended` bool default false.
`createdAt` / `updatedAt` Instant.

### flag (internal only)

No public explorer route reads this until the Phase 0 precision number exists and is >= 20%.
`id` uuid.
`itemId` uuid.
`kind` text.
`state` detected | internal_review | notified | published | resolved | retracted.
`detectedAt` Instant.
`notifiedAt` Instant nullable.
`publishAfter` Instant nullable.
`publishedAt` Instant nullable.
`delta` text.
`sourceUrl` text.
`snapshotId` text.
`methodologyVersion` text.
`replyText` text nullable.
`repliedAt` Instant nullable.
`suspended` bool default false.
`createdAt` / `updatedAt` Instant.

Notify hold is 7 days: `publishAfter = notifiedAt + 7 days`.
Replies store unedited.

## ClickHouse facts

One wide item-fact table for later analytical reads.
Same grain as `item`.
`unidade_canonica` matches Postgres `unidadeCanonica`.
`valor_unitario_base` and `valor_por_unidade_canonica` match Postgres `valorPorUnidadeCanonica`.
C# may package ClickHouse.Client.
Explorer queries Postgres first.

## Landing

Immutable content-hashed parquet under object storage.
Partition by source / date.
Python writes.
C# never writes landing.

TCE-SP monthly LICITACOES CSVs land under `tce_sp_licitacao/date=`.
That source is internal.
Participant CNPJ and Valor da Proposta stay in landing parquet.
The explorer does not read this source.
Cubo SQL is not used.

TCE-RS LicitaCon files land under `tce_rs_licitacon/date=`.
That source is internal.
Participant documents and proposal values stay in landing parquet.
The explorer does not read this source.
Live CKAN is gated by `TCE_RS_FETCH`.

## Explorer API

Shared `PageRequest` / `SkipTake`.
Server-side page every list.
No scoring.
No public flags.
No ranking.

- `GET /api/orgaos`
- `GET /api/orgaos/{id}`
- `GET /api/fornecedores`
- `GET /api/fornecedores/{id}`
- `GET /api/contratacoes`
- `GET /api/contratacoes/{id}`
- `GET /api/items`
- `GET /api/items/{id}`

Internal publication routes exist and are tested.
`GET /api/internal/flags` lists warehouse facts by kind, state, itemId, skip, and take.
That list is not linked from the explorer.
No explorer route may return a flag field.
Phase 0 precision is 9 percent, so public flags stay gated.

Flag copy, if a DTO exists, is "indicio requiring verification" only.

## Framing

Publish delta + source.
Never a verdict label.
Rank orgaos and fornecedores only when ranking exists, never individuals.
No party-level aggregation.
