# Phase 0 notes

Municipio chosen: Volta Redonda, RJ, IBGE 3306305, year 2024.
Population is about 274k (IBGE 2022), inside the 100k-500k mid-size band, and it is not a capital.
The 2024 COMPRA file has 57,384 municipal rows across 731 distinct municipio names.
Volta Redonda has 964 municipal contratacoes (959 unique id_compra), the highest volume among clearly mid-size non-capital cities after excluding Uberlandia / Ribeirao Preto which sit above 500k.
Other candidates present with volume: Bauru 736, Caxias do Sul 577, Maringa 425, Taubate 384, Joinville 346, Campina Grande 276, Londrina 257, Niteroi 238.

## Bulk repo layout

https://repositorio.dados.gov.br/seges/comprasgov/ has anual/, mensal/, diario/, catalogo_cnbs/, compras_legado/.
Annual 2024 files used:
- comprasGOV-anual-VW_FT_PNCP_COMPRA-2024.csv (297M)
- comprasGOV-anual-VW_FT_PNCP_COMPRA_ITEM-2024.csv (870M, streamed)
Annual 2025 ITEM is 4G and was not downloaded.
catalogo_cnbs/ has catmat.csv (120M, semicolon) and catser.csv (509K, semicolon).
https://repositorio.dados.gov.br/seges/comprasnet_contratos/ is the contracts dump (latest plus year folders). It was listed but not needed for this slice.

COMPRA esfera_id values in 2024: F 142944, E 90539, M 57384, N 3737, D 2144.

## Filtering

COMPRA was downloaded and scanned with Polars.
Municipal rows (esfera M) were aggregated by municipio + UF + IBGE.
ITEM was HTTP-streamed with the csv module and filtered to id_compra in the RJ municipal 2024 set (7,184 compras, 43,590 items kept of 1,642,583 national rows).
The analysis slice is the Volta Redonda subset of that pool.
Peer groups use all RJ municipal 2024 items so "same UF" is not vacuous.

## CATMAT coverage

Join is exact integer match of item.cod_item_catalogo to catmat.codigoItem or catser.codigoServico.
No description fuzzy match.
Result on the Volta Redonda 2024 item slice: n_items=5463, n_with_catmat=4464, n_with_catser=396, n_both=394, n_no_code=997, n_code_present_but_unmatched=0, n_free_text_only=997, percent_coded=81.75.
Every non-null code on this municipal slice joined. The 18.25% gap is missing codes, not bogus codes.
National ITEM header rows sometimes show small integers such as 116.0; that pattern did not appear here.
394 codes sit in both catalogs because the published CATMAT and CATSER files share 2,788 codigo values.

## Outlier method

Peer group: valid catalog code if the exact join succeeded, otherwise the same normalized description; plus UF=RJ; plus calendar quarter from data_resultado/data_inclusao; plus quantity band (1, 2-10, 11-100, 101-1000, 1001+).
Robust center and scale: median and MAD. Never mean or sigma.
Score is |unit_price - median| / MAD. If MAD is 0, score is unit_price / median.
Unit price prefers valor_unitario_resultado, else valor_unitario_estimado. Rows without a positive price are not ranked.
Data-error screen: quantidade * unit_price vs valor_total (resultado fields preferred) with tolerance max(R$0.05, 1% of total).
Naive top 100 contained 0 data-error rows; they are labeled in the data_error column and left in rank order.
VR priced items scored: 5462. Data-error priced rows: 0.

## Caveats

Peer n can be 1 when a description is unique in that quarter and quantity band; those rows get a low or undefined deviation and rarely enter the top 100 unless MAD is 0 and the ratio is large inside a tiny group.
Quantity bands are coarse. A 50-unit buy is grouped with 11-100, not with a 1-unit buy of the same item.
This feed is Compras.gov.br, not the full PNCP. Coverage is federal plus the state and municipal entities that publish here (731 municipal names in 2024 COMPRA), not every Brazilian city.
2024 is the first year of centralized municipal item-level data after Lei 8.666/93 repeal. Completeness is incomplete by law for municipios under 20k until 31 Mar 2027, and even larger cities may publish only some orgaos.
TCU Acordao 53/2025 reported high inconsistency rates in PNCP. Arithmetic mismatches are labeled, not treated as price fraud.
CPF values in fornecedor identifiers are masked as ***.XXX.XXX-**. Raw CPF is not stored.
No accusatory label is attached to any orgao or fornecedor. These are statistical deviations for the Phase 0 precision gate.

## Artifacts

- /workspace/compras/phase0/slice-meta.json
- /workspace/compras/phase0/outliers-top100.csv
- /workspace/compras/phase0/catmat-coverage.json
- /workspace/compras/phase0/notes.md
