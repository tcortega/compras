# Phase 0 item 5. TCE-SP and TCE-RS bid-participant proposal fields.

Probed on 20 Aug 2026 00:35 UTC (02:35 Europe/Rome).
No repo was cloned.
Claims were checked against downloaded files, not assumed from the brief.

## Verdict

TCE-SP public monthly Licitacoes extracts expose participant CNPJ and proposed values for classified losers and winners.
TCE-SP cubo SQL (audesp_fase_iv) does not expose participant proposal values.
TCE-RS LicitaCon open data is designed to expose participant proposal values in PROPOSTA, LOTE_PROPOSTA, and ITEM_PROPOSTA.
TCE-RS live CKAN dumps were not opened from this host because dados.tce.rs.gov.br TLS handshake fails with unexpected EOF.
TCE-RS field keys below come from the official eValidador leiaute PDF plus the official example remessa ZIP, which were downloaded and opened.

## TCE-SP public portal and files

Listing page: https://transparencia.tce.sp.gov.br/conjunto-de-dados
The page states that the Fase IV cube is a dimensional model of licitacoes and contratos and that AJUSTES and LICITACOES files are raw extracts from Jan 2018.
Monthly licitacao ZIP (opened): https://transparencia.tce.sp.gov.br/sites/default/files/conjunto-dados/licitacoes-contratos/licitacao-2025-01.zip
2018 licitacao ZIP (header opened): https://transparencia.tce.sp.gov.br/sites/default/files/conjunto-dados/licitacoes-contratos/licitacao-2018_0.zip
Layout PDF (opened): https://transparencia.tce.sp.gov.br/sites/default/files/conjunto-dados/licitacoes-contratos/layout-ajustes-licitacoes.pdf
Cubo schema PDF (opened): https://transparencia.tce.sp.gov.br/sites/default/files/conjunto-dados/licitacoes-contratos/cubo_audesp_fase_iv.pdf
Cubo PostgreSQL dump (header opened): https://transparencia.tce.sp.gov.br/sites/default/files/conjunto-dados/licitacoes-contratos/cubo_audesp_fase_iv.sql_.gz
Latest monthly file listed on the page at probe time: https://transparencia.tce.sp.gov.br/sites/default/files/conjunto-dados/licitacoes-contratos/licitacao-2025-12.zip
Format of licitacao files: ZIP containing one UTF-8 CSV delimited by semicolon.
2025-01 ZIP is 28312912 bytes and expands to licitacao-2025-01_0.csv at 1450417300 bytes with 4117679 data rows.
2018 ZIP is 168214554 bytes, last-modified Fri 13 Nov 2020 19:11:20 GMT, and the inner CSV starts as licitacao-2018_0.csv with the same 21 column names as 2025-01.
Auth: none.
Pagination: none (bulk file per month or year).
Rate limit: none published.
HTTP server sends Accept-Ranges: bytes and Cache-Control: max-age=31536000.
No public read API for these licitacao rows was found.
AUDESP recepcao API at https://audesp.tce.sp.gov.br/api/ is a JWT-protected submit API for jurisdicionados, not a public extract.

## TCE-SP cubo versus monthly extract

Cubo schema is PostgreSQL schema audesp_fase_iv.
Cubo tables present in the dump header: dm_ajuste, dm_contratada, dm_data, dm_entidade, dm_licitacao, dm_mod_inst, dm_municipio, dm_orgao, dm_tipos, dm_tp_objeto, ft_fase4, sa_df_ur.
ft_fase4 measures are qtde_notas_empenho, valor_total_licitacao, valor_ajuste, valor_total_licitacao_ponderado.
dm_contratada has cont_tp_doc, cont_num_doc, cont_nome (awarded contractor, not bidder list).
No cubo table named participante, proposta, or licitante was present in the opened dump header.
The page lists cubo_audesp_fase_iv.sql_.gz as 11/08/2020 and 140.11 MB, so the cube dump is stale relative to the 2025 monthly CSVs.
Use the monthly LICITACOES CSVs, not the cube dump, for participant proposal values.

## TCE-SP participant fields (quoted from the opened CSV header)

Município
Entidade
Código da Licitação
Modalidade de licitação
Objeto
Descrição do objeto contratado
Produto (item)
Quantidade do objeto contratado (item)
Unidade do objeto contratado
Valor unitário orçamento estimativo lote
Quantidade orçamento estimativo lote
Unidade de medida orçamento estimativo lote
Valor unitário orçamento estimativo item
Quantidade orçamento estimativo item
Unidade de medida orçamento estimativo item
Número do edital
Data do edital
CNPJ do participante candidato
Nome do participante candidato
Resultado da Habilitação
Valor da Proposta

Exact header string from licitacao-2025-01_0.csv: "Município";"Entidade";Código da Licitação;"Modalidade de licitação";"Objeto";"Descrição do objeto contratado";"Produto (item)";Quantidade do objeto contratado (item);"Unidade do objeto contratado";Valor unitário orçamento estimativo lote;Quantidade orçamento estimativo lote;"Unidade de medida orçamento estimativo lote";Valor unitário orçamento estimativo item;Quantidade orçamento estimativo item;"Unidade de medida orçamento estimativo item";"Número do edital";"Data do edital";"CNPJ do participante candidato";"Nome do participante candidato";"Resultado da Habilitação";Valor da Proposta
Those 21 names are UTF-8 and include acute accents and cedillas as shown above.
2018 header matches those 21 names exactly.

## TCE-SP field-by-field checklist

Bidder CNPJ: present as CNPJ do participante candidato.
Proposed value: present as Valor da Proposta and is not winner-only.
Rank: absent.
Winner flag: present as Resultado da Habilitação value Classificado - Vencedor.
Proposal date: absent (only Data do edital exists).
Item id: no stable numeric item id (Produto (item) is free text and is often empty).

## TCE-SP sample evidence

In the first 250000 rows of licitacao-2025-01_0.csv, Resultado da Habilitacao counts were Classificado 104701, Proposta nao analisada 50761, Desclassificado 42930, Classificado - Vencedor 24581, Nao Compareceu 12319, Habilitado 6146, empty 5593, Inabilitado 2966, Desistiu 3.
In that slice, 243522 rows had a non-empty Valor da Proposta and 218951 of those were not Vencedor.
In that slice, 244369 document numbers had 14 digits and 0 had 11 digits, so no CPF appeared there.
Aguas de Lindoia bid 2024000000105 item PLAYGROUND INFANTIL UN has six-plus bidders with distinct Valor da Proposta, including winner ROTOcycle 34.914.897/0001-80 at 7220,0 and classified loser MULTKAP 11.021.249/0001-08 at 32250,0.
2018 Adamantina Camara bid 2018000000001 already has the same columns: winner Cooper Card 05.938.780/0001-39 Valor da Proposta 39600,0 and two Nao Compareceu rows at 0,0.

## TCE-SP blockers

None for bulk ingest of monthly CSVs.
The cube dump is the wrong artifact for collusion work because it stores awarded contractor and contract value, not losing bids.
Update cadence on the listing page is Esporadica, so ingest must hash files and not assume daily refresh.
Item-level join is weak because Produto (item) is optional free text and there is no NR_ITEM.

## TCE-RS public portal and files

Open data portal: https://dados.tce.rs.gov.br/
Annual packages: https://dados.tce.rs.gov.br/dataset/licitacoes-consolidado-2026 and the same slug for 2025, 2024, 2023.
CKAN API (documented by the portal, not opened here): https://dados.tce.rs.gov.br/api/3/action/package_show?id=licitacoes-consolidado-2025
2025 resource name quoted on the portal page: licitacoes-consolidado-2025.csv.zip
Portal text: 14 CSV files follow the eValidador LicitaCon leiaute plus CD_ORGAO.
Portal file list: PESSOAS, MEMBRO_CONSORCIO, COMISSAO, MEMBRO_COMISSAO, LICITACAO, LICITANTE, DOTACAO_LICITACAO, EVENTO_LICITACAO, LOTE, ITEM, PROPOSTA, LOTE_PROPOSTA, ITEM_PROPOSTA, DOCUMENTO_LICITACAO.
Portal text: current year and previous year update daily, older years weekly.
Leiaute PDF (opened): https://tcers.tc.br/repo/cex/licitacon/cpt/eValidador_LicitaCon_Manual_Leiaute_1.4.pdf
Diagram PDF (opened): https://tcers.tc.br/repo/cex/licitacon/diagrama_licitacao.pdf
Docs page: https://tcers.tc.br/sistemas-de-controle-externo/?section=LICITACON
Official example remessa ZIP (opened): https://tcers.tc.br/repo/cex/licitacon/cpt/eValidador-licitacon-exemplos-1.4.zip
Citizen search UI: https://portal.tce.rs.gov.br/aplicprod/f?p=50500:19
Jurisdicionado support API swagger (not a proposal dump): https://portal.tce.rs.gov.br/api/qonws/swagger-ui/index.html#/licitacon
eValidador remessa format opened here: pipe-delimited TXT, first line is remessa header CNPJ|inicio|fim|geracao|nome_orgao|n_registros, then data rows.
Open data CSV delimiter was not verified because the CKAN ZIP was not downloaded.
Auth for open data: none stated.
Pagination: none for the annual ZIP.
Rate limit: none published.
IN 13/2017 art. 8 (opened via search and leiaute cross-check): for Pregao, Leilao, Concurso, and Lei 13.303/2016 only the winner proposal is mandatory.

## TCE-RS participant keys (quoted from leiaute tables 9, 14, 15, 16 and matched to example remessa column counts)

LICITANTE.TXT: NR_LICITACAO, ANO_LICITACAO, CD_TIPO_MODALIDADE, TP_DOCUMENTO_LICITANTE, NR_DOCUMENTO_LICITANTE, TP_DOCUMENTO_REPRES, NR_DOCUMENTO_REPRES, TP_CONDICAO, TP_RESULTADO_HABILITACAO, BL_BENEFICIO_MICRO_EPP
PROPOSTA.TXT: NR_LICITACAO, ANO_LICITACAO, CD_TIPO_MODALIDADE, TP_DOCUMENTO_LICITANTE, NR_DOCUMENTO_LICITANTE, DT_PROPOSTA, TP_RESULTADO_PROPOSTA, VL_TOTAL_PROPOSTA, PC_DESCONTO, VL_NOTA_TECNICA, DT_HOMOLOGACAO, PC_TX
LOTE_PROP.TXT: NR_LICITACAO, ANO_LICITACAO, CD_TIPO_MODALIDADE, TP_DOCUMENTO_LICITANTE, NR_DOCUMENTO_LICITANTE, NR_LOTE, PC_DESCONTO, VL_TOTAL_LOTE, VL_NOTA_TECNICA, DT_HOMOLOGACAO, TP_RESULTADO_PROPOSTA, PC_TX, TP_RESULTADO_HABILITACAO
ITEM_PROP.TXT: NR_LICITACAO, ANO_LICITACAO, CD_TIPO_MODALIDADE, TP_DOCUMENTO_LICITANTE, NR_DOCUMENTO_LICITANTE, NR_LOTE, NR_ITEM, PC_BDI, PC_DESCONTO, PC_ENCARGOS_SOCIAIS, VL_UNITARIO, VL_TOTAL_ITEM, VL_NOTA_TECNICA, DT_HOMOLOGACAO, TP_RESULTADO_PROPOSTA, PC_TX, TP_RESULTADO_HABILITACAO
Winner document on LICITACAO, LOTE, and ITEM is NR_DOCUMENTO_VENCEDOR with TP_DOCUMENTO_VENCEDOR.
Open data adds CD_ORGAO according to the portal; that extra column is not in the eValidador example remessa.

## TCE-RS field-by-field checklist

Bidder CNPJ: present as NR_DOCUMENTO_LICITANTE when TP_DOCUMENTO_LICITANTE=J.
Bidder CPF: present as NR_DOCUMENTO_LICITANTE when TP_DOCUMENTO_LICITANTE=F (mask at ingest).
Proposed value: present as VL_TOTAL_PROPOSTA, VL_TOTAL_LOTE, VL_UNITARIO, VL_TOTAL_ITEM and is not winner-only in the example remessa.
Rank: absent.
Winner flag: no dedicated boolean; use TP_RESULTADO_PROPOSTA C/D/P plus NR_DOCUMENTO_VENCEDOR on LICITACAO/LOTE/ITEM.
Proposal date: present as DT_PROPOSTA (dd/mm/aaaa).
Item id: present as NR_ITEM with NR_LOTE and the bid key.

## TCE-RS sample evidence (official example remessa, orgao 89550032000174 ORGAO NAO AUDITADO)

Example PROPOSTA row for bid 42/2014 CNC: J 03722885000120 DT_PROPOSTA 15/10/2014 TP_RESULTADO_PROPOSTA C VL_TOTAL_PROPOSTA 5493164,86.
Same bid losing row: J 91549055000100 DT_PROPOSTA 15/10/2014 TP_RESULTADO_PROPOSTA D VL_TOTAL_PROPOSTA 5493164,86.
ITEM_PROP has 186 data rows and all 186 have VL_UNITARIO and VL_TOTAL_ITEM filled.
ITEM_PROP has 58 items with more than one bidder in the example file.
LICITANTE has 36 data rows, including representative CPFs that were masked in the JSON sample.
TP_RESULTADO_HABILITACAO values in the example: H, I, or empty (leiaute values H habilitado, I inabilitado, N nao compareceu).
TP_RESULTADO_PROPOSTA values in the example: C, D, or empty (leiaute values C classificado, D desclassificado, P pendente).

## TCE-RS blockers

dados.tce.rs.gov.br and portal.tce.rs.gov.br TLS from this host fail with OpenSSL unexpected EOF, so the production annual ZIP was not downloaded.
tcers.tc.br served the leiaute PDF, diagram PDF, and example remessa ZIP without TLS failure.
Open data CSV delimiter, presence of CD_ORGAO, and live fill rates for losing Pregao proposals remain unverified until the CKAN ZIP can be opened.
Pregao and Lei 13.303 coverage of losing bids is optional by rule, so live fill rate must be measured per modalidade after the ZIP is in hand.
