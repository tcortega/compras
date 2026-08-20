# Warehouse and API contract

Python never calls C#.
C# never runs a detector.
Postgres holds canonical entities.
ClickHouse holds analytical item facts.
The explorer may start on Postgres.

## Identity

Phase 0 precision slice: Volta Redonda, RJ, IBGE 3306305, year 2024.
The published explorer slice also lands Niterói, RJ, IBGE 3303302, Bauru, SP, IBGE 3506003, Caxias do Sul, RS, IBGE 4305108, Joinville, SC, IBGE 4209102, Uberlândia, MG, IBGE 3170206, Londrina, PR, IBGE 4113700, Feira de Santana, BA, IBGE 2910800, Caruaru, PE, IBGE 2604106, Anápolis, GO, IBGE 5201108, Vila Velha, ES, IBGE 3205200, Campina Grande, PB, IBGE 2504009, Caucaia, CE, IBGE 2303709, Imperatriz, MA, IBGE 2105302, Arapiraca, AL, IBGE 2700300, Dourados, MS, IBGE 5003702, Marabá, PA, IBGE 1504208, Várzea Grande, MT, IBGE 5108402, Ji-Paraná, RO, IBGE 1100122, Parnamirim, RN, IBGE 2403251, Cruzeiro do Sul, AC, IBGE 1200203, Santana, AP, IBGE 1600600, Rorainópolis, RR, IBGE 1400472, Maringá, PR, IBGE 4115200, Taubaté, SP, IBGE 3554102, Cascavel, PR, IBGE 4104808, Juiz de Fora, MG, IBGE 3136702, Foz do Iguaçu, PR, IBGE 4108304, Santa Maria, RS, IBGE 4316907, Montes Claros, MG, IBGE 3143302, Governador Valadares, MG, IBGE 3127701, Canoas, RS, IBGE 4304606, Lages, SC, IBGE 4209300, Santarém, PA, IBGE 1506807, Rio Verde, GO, IBGE 5218805, Paulo Afonso, BA, IBGE 2924009, São Lourenço da Mata, PE, IBGE 2613701, Crato, CE, IBGE 2304202, Ariquemes, RO, IBGE 1100023, Colatina, ES, IBGE 3201506, Castanhal, PA, IBGE 1502400, Divinópolis, MG, IBGE 3122306, Petrópolis, RJ, IBGE 3303906, Ipatinga, MG, IBGE 3131307, Macaé, RJ, IBGE 3302403, Santa Luzia, MG, IBGE 3157807, Nova Friburgo, RJ, IBGE 3303401, Marília, SP, IBGE 3529005, Balneário Camboriú, SC, IBGE 4202008, Itaquaquecetuba, SP, IBGE 3523107, Praia Grande, SP, IBGE 3541000, São José dos Pinhais, PR, IBGE 4125506, Suzano, SP, IBGE 3552502, Guarujá, SP, IBGE 3518701, Cotia, SP, IBGE 3513009, Parauapebas, PA, IBGE 1505536, Jacareí, SP, IBGE 3524402, Itaboraí, RJ, IBGE 3301900, and Maricá, RJ, IBGE 3302700, years 2024, 2025, and 2026 YTD, from official Compras.gov.br anual COMPRA and ITEM files partitioned by source/year/date.
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

### cnae

Official Receita CNAE lookup landed from the same dump as estabelecimentos.
`codigo` text primary key, digits only.
`descricao` text from the RFB Cnaes file.
Python writes.
C# joins `fornecedor.cnae` by digits.
Missing rows leave the description null.
Do not invent a description.

### fornecedor_socio

Public-record QSA rows for slice fornecedores.
This is E2 factual enrichment, not F1 `fornecedor_adjacency`.
Undirected public names only.
No score, no shared-partner count, no adjacency kind.
`id` uuid.
`fornecedorId` uuid FK fornecedor.
`fornecedorCnpj` text.
`nome` text.
`cpfMasked` text nullable.
PF socios store the ingest mask `***.XXX.XXX-**`.
PJ socios leave `cpfMasked` null.
Raw CPF is forbidden.
`qualificacao` text nullable, resolved from RFB Qualificacoes when that code landed, otherwise the source code.
Python writes from landed `receita_cnpj_socios` after CPF mask.
C# reads.
GET `/api/fornecedores/{id}` returns these rows.
GET `/api/fornecedores` does not.

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
`specConcentracao` text nullable.
`specDosagem` text nullable.
`specTamanho` text nullable.
These spec fields store the raw extracted token from the item description.
Unknown or absent spec tokens stay null.
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
A caixa or pacote with an explicit count uses that count as `to_base_factor` and the inner unit as canonical.
A caixa or pacote without a count keeps the catalog row (`CX` stays `cx`, factor 1).
`uf` text.
`quarter` text.
`snapshotId` text.
`methodologyVersion` text.
`suspended` bool default false.
`createdAt` / `updatedAt` Instant.

### flag (internal only)

No public explorer route reads this until the Phase 0 precision number exists and is >= 20%.
`kind` is a detector name.
`cnpj_age` is the flag tier when `award_date` minus `opened_on` is under 90 days.
`cnpj_age_info` is the info tier when that age is at least 90 days and under 365 days.
`fracionamento` is the Art. 75 §1 same-object annual aggregate when every dispensa purchase in the órgão+CATMAT-class+year group stays under the year+kind threshold and the sum exceeds it.
`fracionamento_cluster` is the sprint cluster: at least three dispensas in that group, each in the last tenth under the limit, all award dates inside a 90-day window.
The aggregate key prefers `codigo_classe`, then `codigo_grupo`, then the CATMAT/CATSER class/group join, then the item code.
Threshold amounts live in `detect/compras_detect/data/dispensa_thresholds.csv` and are not Python literals.
All of these kinds stay `state=detected` and are not public alerts.
`id` uuid.
`itemId` uuid.
`kind` text.
`state` detected | internal_review | notified | published | resolved | retracted.
`detectedAt` Instant.
`notifiedAt` Instant nullable.
`notifyArtifact` text nullable.
`publishAfter` Instant nullable.
`publishedAt` Instant nullable.
`delta` text.
`sourceUrl` text.
`snapshotId` text.
`methodologyVersion` text.
New pipeline writes stamp `methodologyVersion` 0.2 on flags.
An existing flag row keeps its prior stamp because `write_flags` ON CONFLICT updates delta only.
API FullCycle fixtures stay on 0.1 so the frozen suite does not rewrite historical rows.
Phase 0 and A3 label files stay on phase1-0.1.0.
`replyText` text nullable.
`repliedAt` Instant nullable.
`suspended` bool default false.
`createdAt` / `updatedAt` Instant.

Notify hold is 7 days: `publishAfter = notifiedAt + 7 days`.
Notify accepts an optional artifact (url or filename) and stores it as `notifyArtifact`.
Notify is a manual record that a notice was sent.
No email is sent.
No SMTP.
No orgao contact registry.
Replies store unedited.
Legal state edges are enforced in Postgres.
detected to internal_review.
internal_review to notified.
notified to published.
published to resolved.
published to retracted.
No reverse.
No other jump.
Notify hold stays in C#.
A legal INSERT or UPDATE writes `flag_audit`.
Columns: flagId, fromState (null on create into detected), toState, at, actor `internal/staging`, optional reason/delta.

### flag_audit (internal only)

One row per successful transition, including create into detected.
No explorer route reads this.

### catalog_code

`codigo` text.
`kind` catmat | catser.
Composite primary key.
Python writes from landed CATMAT/CATSER.
C# joins `item.catmat` / `item.catser` as exact integers.

### landing_source

`name` text primary key.
`lastUpdate` Instant nullable.
`n` int.
`snapshotId` text nullable.
Python writes from landing manifests.
C# does not invent a timestamp.

### item_exclusion (internal only)

These are data-quality tags, not public alerts.
Excluded items leave the price-anomaly pool and stay in `item`.
They remain on GET /api/items.
No explorer route may return an exclusion reason.
Closed reason set: qty_unit_price_neq_total, decimal_shift, qty_eq_1_collapse, zero_or_negative, duplicate_row, catalog_magnitude.
`itemId` uuid FK item.
`reason` text.
`detail` text.
`snapshotId` text.
`methodologyVersion` text.
`createdAt` timestamptz.
Python writes this table after normalize.
C# does not run a detector.

### fornecedor_adjacency (internal only)

Shared-QSA-partner, shared-address, and shared-phone/email edges from landed Receita CNPJ dumps.
This is F1 groundwork, not F2 co-bid, not E2 public enrichment, and not a public alert.
Shared partners are not per se illegal (TCU 297/2009, 1.793/2011, 2.803/2016).
No explorer route reads this table.
No explorer DTO carries adjacency, shared-partner counts, or a score.
C# does not run this detector.
Python writes from landed Receita frames after CPF mask.
`kind` is shared_qsa_partner | shared_address | shared_phone | shared_email.
`leftCnpj` and `rightCnpj` are 14-digit CNPJs stored once per undirected pair, with leftCnpj < rightCnpj.
Unique (kind, leftCnpj, rightCnpj).
`evidence` never stores raw CPF.
A socio key is the ingest mask `***.XXX.XXX-**` or a legal-entity socio CNPJ.
Address is fold/ascii tipo+logradouro, numero, digit CEP, and municipio.
Rows with an empty street, or with neither numero nor CEP, are skipped.
Phone is digits of DDD plus number.
Email is fold/ascii.
Empty phone and email values are skipped.
Tokens that look like CPF are masked or dropped.
`snapshotId` is the Receita landing sha256.
`methodologyVersion` is the pipeline version.
`createdAt` timestamptz.

### licitacao_participante (internal only)

Participant proposal rows from TCE-SP and TCE-RS landing.
UF is SP or RS.
source is tce_sp or tce_rs.
TCE-PR, TCE-PE, and TCE-RJ have no official public participant-proposal extract and are ignored.
`participante` is a 14-digit CNPJ or the ingest CPF mask.
Raw CPF is never stored.
`itemLote` is the item or lote key when the source has one.
`snapshotId` is the landing sha256 or the fixture stamp.
No explorer route reads this table.

### co_bid_edge (internal only)

Undirected co-presence on one licitacao+item/lote.
`kind` is `co_bid`.
`leftCnpj` < `rightCnpj`.
Stores both proposed values and the winner token when one of the pair won.
A co-bid edge is not a finding.
No explorer route reads this table.
C# does not run this detector.

### co_bid_screen (internal only)

Internal CADE screens on SP/RS warehouse participants.
Kinds are `bid_variance`, `skew`, `cover_bidding`, and `winner_rotation`.
State starts at `detected`.
`evidence` is JSON and always includes framing `indicio a verificar`.
`methodologyVersion` is 0.2.
Thresholds live in `detect/compras_detect/data/cade_screens.csv`.
Those numbers are an internal heuristic, not a legal test.
No CADE or TCU published numeric cutoff was found for these screens.
No explorer route reads this table.
No explorer DTO carries these kinds.

The CATMAT/CATSER classifier is internal normalize.
It fills only rows with no official catalog code.
Assigned `knn` codes are not public alerts.
Phase 0 CATMAT coverage on Volta Redonda 2024 stays 81.75 percent.
That measured gap is not rewritten as if the classifier already ran on VR.

## ClickHouse facts

One wide item-fact table for later analytical reads.
Same grain as `item`.
`unidade_canonica` matches Postgres `unidadeCanonica`.
`valor_unitario_base` and `valor_por_unidade_canonica` match Postgres `valorPorUnidadeCanonica`.
`spec_concentracao`, `spec_dosagem`, and `spec_tamanho` match the nullable Postgres spec columns.
C# may package ClickHouse.Client.
Explorer queries Postgres first.

## Landing

Immutable content-hashed parquet under object storage.
Partition by source / date.
Python writes.
C# never writes landing.

TCE-SP monthly LICITACOES CSVs land under `tce_sp_licitacao/date=`.
That source is internal.
Participant CNPJ and Valor da Proposta land in parquet and persist to `licitacao_participante`.
The explorer does not read this source.
Cubo SQL is not used.

TCE-RS LicitaCon files land under `tce_rs_licitacon/date=`.
That source is internal.
Participant documents and proposal values land in parquet and persist to `licitacao_participante`.
The explorer does not read this source.
Live CKAN is gated by `TCE_RS_FETCH`.

PNCP consulta lands under `pncp_consulta/date=` with a resumable `_cursor.json` or `_gaps_cursor.json`.
A background Dagster job (`pncp_consulta_gaps_run`, America/Sao_Paulo) fetches only gaps for the already covered 59 IBGE codes.
A gap is a consulta compra, item, or later page that the Compras.gov.br bulk does not already give that IBGE.
Complete compras.gov rows are not re-fetched.
Warehouse reads those gap rows as normal itens and contratacoes.
The explorer does not label them as gaps.
Live HTTP stays on `pncp.gov.br` with 1s spacing and exponential backoff on 429/5xx.
Fixture mode never calls `resolve_pncp_consulta`.

CGU CEIS and CNEP bulk CSVs land under `cgu_ceis_cnep/date=`.
That source is internal.
Sanction windows stay in landing parquet.
The explorer does not read this source.
Live Portal da Transparência download is gated by `SANCTIONS_FETCH`.

## Explorer API

Shared `PageRequest` / `SkipTake`.
Server-side page every list.
No scoring.
No public flags.
No ranking.

- `GET /api/orgaos`
- `GET /api/orgaos/{id}`
- `GET /api/fornecedores`
- `GET /api/fornecedores/{id}` returns the list fields plus `cnaeDescricao` when the CNAE table has that code, `idadeCadastral` as a duration from `openedOn` to a stated `idadeAsOf` civil date, and `qsa` names with masked CPF.
List items do not carry `qsa`.
Company age is cadastral duration, not a risk signal.
Null `openedOn` returns `idadeCadastral` `n/d`.
Empty QSA is an empty array.
- `GET /api/contratacoes`
- `GET /api/contratacoes/{id}`
- `GET /api/items`
- `GET /api/items/{id}`
- `GET /api/busca` reads the Meilisearch index of `item.descricao`, `fornecedor.razaoSocial`, and `orgao.razaoSocial`.
Documents are factual text only.
The document primary key is `{kind}_{entityId}` so re-sync is idempotent and Meilisearch accepts the identifier.
No flag fields, no detector scores, no adjacency, and no CPF.
Empty `q` keeps the slice coverage denominator and invents no hits.
A mixed-UF search leaves `coverage.uf` empty.
When `MEILI_URL` is unset or Meilisearch is down the handler returns empty pages and `source` is `unset` or `unavailable`.
It does not invent hits.
- `GET /api/cobertura` returns municípios ingeridos (nome, uf, ibge), years, row counts, live CATMAT exact-integer catalog join (`catmatCoveragePercent`, `nCoded`, `nItems`), per-source landing freshness (`compras_gov`, `receita_cnpj`, `ocds`, `pncp_consulta`, `tce_sp`, `tce_rs`, `cgu_ceis_cnep`), and the coverage denominator.
A mixed-UF slice leaves `coverage.uf` empty.
It is not a national total.
Empty sources return `lastUpdate` null and `n=0`.
The public CATMAT percent is the warehouse catalog join, not the Phase 0 VR 81.75 label and not the kNN classifier.

Internal publication routes exist and are tested.
`GET /api/internal/flags` lists warehouse facts by kind, state, itemId, skip, and take.
`GET /api/internal/flags/{id}/audit` reads `flag_audit` for that row.
That list is not linked from the explorer.
Staging triage UI lives at `/interno/triagem` and is not in the public shell nav.
No explorer route may return a flag field.
No explorer route may return an exclusion reason.
No explorer route may return adjacency or a shared-partner count.
No explorer route may return a co-bid edge, CADE screen, bid variance, cover-bidding, or winner rotation.
No explorer route may return spec columns or a knn quality token.
Phase 0 precision is 9 percent, so public flags stay gated.

Flag copy, if a DTO exists, is "indicio requiring verification" only.

## Framing

Publish delta + source.
Never a verdict label.
Rank orgaos and fornecedores only when ranking exists, never individuals.
No party-level aggregation.
