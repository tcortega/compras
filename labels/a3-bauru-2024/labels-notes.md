# A3 Bauru 2024 blind labels

Slice is Bauru SP IBGE 3506003 year 2024 municipal non-legislative COMPRA+ITEM from the official 2024 bulk.
This is not Volta Redonda.
All 100 BEFORE source items were fetched from the PNCP item API.
Item path used: /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens/{n}.
Resultados were read when present; 22 items had HTTP 204.
The labeler file was sample-before.csv, which has no outlier score, rank, or exclusion reason.
Scores stay in scores-before.csv and the manifest.
The conservative Phase 0 9 percent rubric was used.
real means the source confirms the CSV price and the peer comparison is the same unit and spec class.
real is a surviving price anomaly, not a fraud verdict.
unit error means the source unit is a pack or scale that the peers are not.
spec difference means the source confirms the price but the item is a different product or job class than the peer key.
data error means no homologated award, or the CSV unit price disagrees with the current PNCP award.
Do not treat a source-matching CSV price as real when the peer class is wrong.
Phase 0 VR 2024 remains 9 real / 9 unit / 35 spec / 47 data.
Phase 0 CATMAT coverage remains 81.75 percent.
No raw CPF was stored.
No accusatory copy is attached to any orgao or fornecedor.

## Counts
n_real 42.
n_unit_error 10.
n_spec_difference 24.
n_data_error 24.
n_unresolved 0.
precision_real 0.42 of labeled rows and 42/100 of the BEFORE pool.
A1 excluded 19 of the BEFORE top 100 (decimal_shift 5, qty_eq_1_collapse 14, duplicate_row 1).
A2 knn filled 233 uncoded Bauru descriptions and changed some AFTER peer keys.
AFTER pool is 100 items; 74 of those already have BEFORE labels and 26 are unresolved because they were not relabeled.
AFTER labeled mix is 34 real / 7 unit / 15 spec / 18 data, precision 34/74.
AFTER real over the 100-row pool is 34/100.
CATMAT exact-join coverage on this Bauru executive slice is 81.78 percent (2412+178-175)/2953.

## Rubric reminders
Source-confirmed prices still get spec difference when CATSER buckets mix jobs or CATMAT codes mix pack sizes and presentations.
Fracassado, Deserto, Anulado/Revogado/Cancelado, and Em andamento without an award are data error.
A later homologated unit price that disagrees with the CSV estimate is data error.
