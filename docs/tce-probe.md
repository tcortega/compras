# TCE participant-field probe

Bid participant data is not in the federal Compras.gov.br item feed.
Collusion detectors need state TCE portals.

## TCE-SP

Portal: https://transparencia.tce.sp.gov.br/conjunto-de-dados
Sample: https://transparencia.tce.sp.gov.br/sites/default/files/conjunto-dados/licitacoes-contratos/licitacao-2025-01.zip
Cube docs: cubo_audesp_fase_iv.pdf (Fase IV). The published cube SQL (ft_fase4) has the awarded contractor only.
The monthly licitacao CSV is the participant file.
Auth: none.
Encoding UTF-8, delimiter `;`, decimal `,`.
Grain: licitacao x item/lote x participante.

Participant proposal values: yes.
Verified keys in licitacao-2025-01_0.csv (same 21 keys in licitacao-2019-01):
- `CNPJ do participante candidato`
- `Nome do participante candidato`
- `Valor da Proposta`
- `Resultado da Habilitação` (`Classificado - Vencedor` is the winner flag)
- `Produto (item)`, `Quantidade do objeto contratado (item)`
- `Código da Licitação` (unique only within Entidade)

Missing: rank, proposal date, numeric item id, CPF column.
No CPF in the first 5605 parsed 2025-01 rows.
Two Adamantina rows on licitacao 2024000000113 show proposed values 5200,0 (vencedor) and 5320,0 (classificado).

## TCE-RS

Portal: LicitaCon open data, e.g. https://dados.tce.rs.gov.br/dataset/licitacoes-consolidado-2025
CKAN: `package_show?id=licitacoes-consolidado-{year}`
Legacy zip pattern: http://dados.tce.rs.gov.br/dados/licitacon/licitacao/ano/{year}.csv.zip
Layout: eValidador LicitaCon 1.4.056 (2026-07-14) at https://tcers.tc.br/repo/cex/licitacon/cpt/eValidador_LicitaCon_Manual_Leiaute_1.4.pdf
Open data zip is 14 CSVs: PESSOAS, LICITACAO, LICITANTE, PROPOSTA, LOTE_PROPOSTA, ITEM_PROPOSTA, and others.

Participant proposal values: yes, in the official leiaute.
- LICITANTE: `NR_DOCUMENTO_LICITANTE`, `TP_DOCUMENTO_LICITANTE` (J CNPJ, F CPF)
- PROPOSTA: `VL_TOTAL_PROPOSTA`, `DT_PROPOSTA`, `TP_RESULTADO_PROPOSTA`
- ITEM_PROPOSTA: `VL_UNITARIO`, `VL_TOTAL_ITEM`, `NR_ITEM`
- Winner lives on LICITACAO / LOTE / ITEM `NR_DOCUMENTO_VENCEDOR` plus `VL_HOMOLOGADO`
- No rank field

Coverage caveat: for PRE, PRP, PDE and several other modalities only the winning proposal is mandatory.
Non-winner proposed values may be absent.
Other modalities require all licitante proposals at encerramento since 07/2019.

Blocker: dados.tce.rs.gov.br HTTPS closed the TLS session (UNEXPECTED_EOF). HTTP HEAD timed out. CKAN and the LicitaCon cidadao page returned 500 via the fetch path used here.
Live 2025 CSVs were therefore not downloaded on this box.
Field names and examples above come from the official leiaute PDF, which did download from tcers.tc.br.
CPF examples in that PDF are stored masked as `***.999.999-**`.

## Implication

Tier 2 collusion screens can use TCE-SP monthly CSVs now.
TCE-RS ingest should retry the zip from another network path or the daily-updated CKAN resource, then join `ITEM_PROPOSTA`.
Neither feed is a rank table.
