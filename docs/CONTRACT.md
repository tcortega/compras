# Warehouse and API contract

Python never calls C#.
C# never runs a detector.
Postgres holds canonical entities.
ClickHouse holds analytical item facts.
The explorer may start on Postgres.

## Identity

Município of the Phase 0 slice: Volta Redonda, RJ, IBGE 3306305, year 2024.
That slice does not limit the schema.

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
`valorUnitario` numeric nullable.
`valorTotal` numeric nullable.
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
C# may package ClickHouse.Client.
Explorer queries Postgres first.

## Landing

Immutable content-hashed parquet under object storage.
Partition by source / date.
Python writes.
C# never writes landing.

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
They are not linked from the explorer.

Flag copy, if a DTO exists, is "indicio requiring verification" only.

## Framing

Publish delta + source.
Never a verdict label.
Rank orgaos and fornecedores only when ranking exists, never individuals.
No party-level aggregation.
