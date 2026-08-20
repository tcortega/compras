# F3 Volta Redonda 2024 internal rollup

This rollup covers the nine Phase 0 labels.csv rows marked real for Volta Redonda RJ IBGE 3306305 year 2024.
It is not a public flag and it does not add an explorer DTO.
real means a surviving price anomaly, not a fraud verdict.
Copy is indicio and factual only.
Shared partners are not per se illegal (TCU 297/2009, 1.793/2011, 2.803/2016).
Phase 0 files stay at 9 real / 9 unit / 35 spec / 47 data and CATMAT 81.75 percent.
Bauru A3 stays on its committed 42/100 before mix and is not this set.
Sprint data+unit-under-15% is not claimed met.

## Method

B1 used compras_detect.tier1.sanctioned.detect_sanctioned on the official 20260820 CEIS and CNEP zips joined to PNCP dataResultado.
B2 used compras_detect.tier1.cnpj_age.detect_cnpj_age with opened_on from public RFB-sourced CNPJ cards and award_date from PNCP dataResultado.
F1 used compras_detect.adjacency.build_adjacencies on the six awarded legal-entity CNPJ cards in this set.
A full RFB dump reverse search was not landed, so an F1 miss here is not a national Receita claim.
Empty cells are misses and were not invented.
Python never calls C#.
C# never runs a detector.
The warehouse remains the only contract.

## Signals that fired

B1 sanctioned_ceis_cnep fired on 0 of 9 rows.
B2 cnpj_age fired on 0 of 9 rows.
B2 cnpj_age_info fired on 1 of 9 rows: 4500680590077202400098 (rank 43, age_days=161, tier=info).
F1 adjacency fired on 0 of 9 rows.

## Cross-signal table

| id_compra_item | rank | B1 | B2 | F1 |
| --- | --- | --- | --- | --- |
| 4500680700113202400020 | 9 |  |  |  |
| 9277610590104202400016 | 11 |  |  |  |
| 4500680590077202400098 | 43 |  | cnpj_age_info |  |
| 4500680590126202400008 | 50 |  |  |  |
| 9268500590078202400042 | 58 |  |  |  |
| 4500680590045202400004 | 59 |  |  |  |
| 4500680590104202400074 | 83 |  |  |  |
| 4500680700113202400010 | 85 |  |  |  |
| 4500680700118202400006 | 100 |  |  |  |

Rank 100 is a PF award stored as ***.861.487-**.
That row has no CNPJ for B1, B2, or F1, so those cells stay empty.
Rank 9 and rank 85 share CNPJ 31848674000174 on the same compra.
Rank 59 and rank 83 share CNPJ 39421287000169.
A repeated CNPJ is not an F1 adjacency kind.

## Official sources

PNCP item and resultados paths on pncp.gov.br.
Portal da Transparencia CEIS and CNEP listings and the 20260820 saida zips on dadosabertos-download.cgu.gov.br.
Public RFB-sourced CNPJ cards via minhareceita.org and brasilapi.com.br.
The RFB share index remains https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9.

## What this is not

This folder does not publish flags.
This folder does not change explorer DTOs.
This folder does not add a city to the explorer.
This folder does not rewrite Phase 0 9 percent or 81.75 percent.
