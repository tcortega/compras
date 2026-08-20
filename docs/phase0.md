# Phase 0 notes

Municipio chosen for the Phase 0 precision gate: Volta Redonda, RJ, IBGE 3306305, year 2024.
Population is about 274k (IBGE 2022), inside the 100k-500k mid-size band, and it is not a capital.
The published explorer fixture also lands municípios that the same 2024 COMPRA file already counted: Niterói, RJ, IBGE 3303302 (238 municipal contratacoes), Bauru, SP, IBGE 3506003 (736), Caxias do Sul, RS, IBGE 4305108 (577), Joinville, SC, IBGE 4209102 (346), Uberlândia, MG, IBGE 3170206 (1152), Londrina, PR, IBGE 4113700 (257), Feira de Santana, BA, IBGE 2910800 (12), Caruaru, PE, IBGE 2604106 (167), Anápolis, GO, IBGE 5201108 (62), Vila Velha, ES, IBGE 3205200 (33), Campina Grande, PB, IBGE 2504009 (225), Caucaia, CE, IBGE 2303709 (83), Imperatriz, MA, IBGE 2105302 (6), Arapiraca, AL, IBGE 2700300 (162), Dourados, MS, IBGE 5003702 (53), Marabá, PA, IBGE 1504208 (233), Várzea Grande, MT, IBGE 5108402 (23), Ji-Paraná, RO, IBGE 1100122 (183), Parnamirim, RN, IBGE 2403251 (52), Cruzeiro do Sul, AC, IBGE 1200203 (56), Santana, AP, IBGE 1600600 (6), Rorainópolis, RR, IBGE 1400472 (6), Maringá, PR, IBGE 4115200 (425), Taubaté, SP, IBGE 3554102 (384), Cascavel, PR, IBGE 4104808 (245), Juiz de Fora, MG, IBGE 3136702 (142), Foz do Iguaçu, PR, IBGE 4108304 (871), Santa Maria, RS, IBGE 4316907 (240), Montes Claros, MG, IBGE 3143302 (67), Governador Valadares, MG, IBGE 3127701 (78), Canoas, RS, IBGE 4304606 (11), Lages, SC, IBGE 4209300 (199), Santarém, PA, IBGE 1506807 (23), Rio Verde, GO, IBGE 5218805 (384), Paulo Afonso, BA, IBGE 2924009 (63), São Lourenço da Mata, PE, IBGE 2613701 (65), Crato, CE, IBGE 2304202 (69), Ariquemes, RO, IBGE 1100023 (222), Colatina, ES, IBGE 3201506 (5), Castanhal, PA, IBGE 1502400 (24), Divinópolis, MG, IBGE 3122306 (332), Petrópolis, RJ, IBGE 3303906 (19), Ipatinga, MG, IBGE 3131307 (62), Macaé, RJ, IBGE 3302403 (182), Santa Luzia, MG, IBGE 3157807 (65), Nova Friburgo, RJ, IBGE 3303401 (154), Marília, SP, IBGE 3529005 (95), and Balneário Camboriú, SC, IBGE 4202008 (74).
Those extra rows use the same landed COMPRA/ITEM schema.
They do not replace the Volta Redonda labeled set.
Jaboatão dos Guararapes, PE, IBGE 2607901, has no municipal row in that 2024 COMPRA file.
Serra, ES, IBGE 3205002, is present in the 2024 COMPRA file only as federal rows.
Vila Velha is the municipal ES replacement with landed volume.
Juazeiro do Norte, CE, IBGE 2307304, is present in the 2024 COMPRA file only as federal rows.
Caucaia is the municipal CE replacement with landed volume.
Ananindeua, PA, IBGE 1500800, is present in the 2024 COMPRA file only as federal rows.
Mossoró, RN, IBGE 2408003, has no municipal row in that 2024 COMPRA file.
Arapiraca is the municipal replacement with landed volume after Ananindeua had only federal rows.
Rondonópolis, MT, IBGE 5107602, has only 4 municipal rows and none with valor_total_homologado.
Parnaíba, PI, IBGE 2207702, is present in the 2024 COMPRA file only as federal rows.
Dourados is the listed municipal MS fallback with landed volume.
Marabá is the municipal PA replacement with landed volume after Ananindeua had only federal rows.
Várzea Grande is the listed municipal MT fallback with landed volume after Rondonópolis had only 4 municipal rows and none with valor_total_homologado.
Ji-Paraná is the listed municipal RO fallback with landed volume after Mossoró had no municipal row and Parnaíba had only federal rows.
Itabaiana, SE, IBGE 2802908, has no municipal row in that 2024 COMPRA file.
Itacoatiara, AM, IBGE 1301902, has no municipal row in that 2024 COMPRA file.
Parnamirim is the municipal RN replacement with landed volume after Mossoró had no municipal row.
Cruzeiro do Sul is the listed municipal AC fallback with landed volume after Parnaíba had only federal rows and Itabaiana and Itacoatiara had no municipal rows.
Nossa Senhora do Socorro, SE, IBGE 2804805, has no row in that 2024 COMPRA file.
Picos, PI, IBGE 2208007, is present in the 2024 COMPRA file only as federal rows.
Lagarto, SE, IBGE 2803501, has no municipal row in that 2024 COMPRA file.
Floriano, PI, IBGE 2203909, has no row in that 2024 COMPRA file.
Parintins, AM, IBGE 1303403, is present in the 2024 COMPRA file only as federal rows.
Brasília, DF, IBGE 5300108, has no municipal row in that 2024 COMPRA file.
Santana is the listed municipal AP fallback with landed volume after Nossa Senhora do Socorro and Lagarto had no municipal SE rows and Picos had only federal rows.
Rorainópolis is the listed municipal RR fallback with landed volume after Floriano had no row, Parintins had only federal rows, and Brasília had no municipal row.
Araguaína, TO, IBGE 1702109, is present in the 2024 COMPRA file only as federal, state, and other non-municipal rows.
Gurupi, TO, IBGE 1709500, is present in the 2024 COMPRA file only as state and other non-municipal rows.
Manacapuru, AM, IBGE 1302504, is present in the 2024 COMPRA file only as federal rows.
Iranduba, AM, IBGE 1301852, is present in the 2024 COMPRA file only as federal rows.
Unused UFs AM, PI, SE, TO, and DF have municipal rows only in small towns, so they have zero mid-size municipal rows in that 2024 COMPRA file.
Maringá is the listed municipal PR fallback with landed volume after those unused UFs had no mid-size municipal row.
Taubaté is the listed municipal SP fallback with landed volume after those unused UFs had no mid-size municipal row.
Pelotas, RS, IBGE 4314407, is present in the 2024 COMPRA file only as federal rows.
Franca, SP, IBGE 3516200, is present in the 2024 COMPRA file only as state rows.
Vitória da Conquista, BA, IBGE 2933307, is present in the 2024 COMPRA file only as federal and state rows.
Petrolina, PE, IBGE 2611101, is present in the 2024 COMPRA file only as federal rows.
Campos dos Goytacazes, RJ, IBGE 3301009, is present in the 2024 COMPRA file only as federal and state rows.
São José do Rio Preto, SP, IBGE 3549805, is present in the 2024 COMPRA file only as state and federal rows.
Blumenau, SC, IBGE 4202404, has only 14 municipal rows, all from the Câmara.
Cascavel is the listed municipal PR fallback with landed volume after those unused UFs still had no mid-size municipal row.
Juiz de Fora is the listed municipal MG fallback with landed volume after those unused UFs still had no mid-size municipal row.
Ponta Grossa, PR, IBGE 4119905, is present in the 2024 COMPRA file only as federal and state rows.
Santos, SP, IBGE 3548500, is present in the 2024 COMPRA file only as state and federal rows.
Sorocaba, SP, IBGE 3552205, is present in the 2024 COMPRA file only as state and federal rows.
Criciúma, SC, IBGE 4204608, is present in the 2024 COMPRA file only as federal rows.
Uberaba, MG, IBGE 3170107, has only 7 municipal rows, all from the municipal pension institute, and no MUNICIPIO DE UBERABA row.
Foz do Iguaçu is the listed municipal PR fallback with landed volume after those unused UFs still had no mid-size municipal row.
Santa Maria is the listed municipal RS fallback with landed volume after those unused UFs still had no mid-size municipal row.
Piracicaba, SP, IBGE 3538709, has 91 municipal rows, all from the Câmara.
Jundiaí, SP, IBGE 3525904, has no municipal row in that 2024 COMPRA file.
Limeira, SP, IBGE 3526902, has no municipal row in that 2024 COMPRA file.
Novo Hamburgo, RS, IBGE 4313409, has no row in that 2024 COMPRA file.
São Leopoldo, RS, IBGE 4318705, has 19 municipal rows, all from the municipal water and sewer service, and no MUNICIPIO DE SAO LEOPOLDO row.
Palhoça, SC, IBGE 4211900, has 11 municipal rows, all from the Câmara.
Itajaí, SC, IBGE 4208203, has 93 municipal rows from the water service, the Câmara, and the port, and no MUNICIPIO DE ITAJAI row.
Montes Claros is the listed municipal MG fallback with landed volume after those unused UFs still had no mid-size municipal row.
Governador Valadares is the listed municipal MG fallback with landed volume after those unused UFs still had no mid-size municipal row.
São José, SC, IBGE 4216602, has 24 municipal rows, all from the Câmara.
Chapecó, SC, IBGE 4204202, is present in the 2024 COMPRA file only as federal rows.
Sete Lagoas, MG, IBGE 3167202, is present in the 2024 COMPRA file only as federal rows.
Passo Fundo, RS, IBGE 4314100, is present in the 2024 COMPRA file only as federal rows.
Gravataí, RS, IBGE 4309209, is present in the 2024 COMPRA file only as federal rows.
Rio Grande, RS, IBGE 4315602, is present in the 2024 COMPRA file only as federal rows.
Cabo Frio, RJ, IBGE 3300704, has no row in that 2024 COMPRA file.
Magé, RJ, IBGE 3302502, has no municipal row in that 2024 COMPRA file.
Canoas is the leftover municipal RS row with landed volume after those unused UFs still had no mid-size municipal row.
Lages is the leftover municipal SC row with landed volume after São José had only Câmara rows, Chapecó had only federal rows, and SC still had only Joinville.
Caxias, MA, IBGE 2103000, is present in the 2024 COMPRA file only as federal rows.
Timon, MA, IBGE 2112209, is present in the 2024 COMPRA file only as federal rows.
Sinop, MT, IBGE 5107909, has no municipal row in that 2024 COMPRA file.
Sobral, CE, IBGE 2312908, has 2 municipal rows from MUNICIPIO DE SOBRAL and none with valor_total_homologado.
Olinda, PE, IBGE 2609600, has 8 municipal rows, all from the Câmara.
Paulista, PE, IBGE 2610707, has 1 municipal row, from the Câmara.
Ilhéus, BA, IBGE 2913606, is present in the 2024 COMPRA file only as federal rows.
Itabuna, BA, IBGE 2914802, is present in the 2024 COMPRA file only as federal and state rows.
Aparecida de Goiânia, GO, IBGE 5201405, has 20 municipal rows from MUNICIPIO DE APARECIDA DE GOIANIA, but the 2022 population sits above the 100k-500k band.
Santarém is the leftover municipal PA row with landed volume after PA still had only Marabá.
Rio Verde is the leftover municipal GO row with landed volume after GO still had only Anápolis.
Paulo Afonso is the leftover municipal BA row with landed volume after BA still had only Feira de Santana.
São Lourenço da Mata is the leftover municipal PE row with landed volume after PE still had only Caruaru.
Crato is the leftover municipal CE row with landed volume after CE still had only Caucaia.
Ariquemes is the leftover municipal RO row with landed volume after RO still had only Ji-Paraná.
Colatina is the leftover municipal ES row with landed volume after ES still had only Vila Velha.
Castanhal is the leftover municipal PA row with landed volume after PA still had Marabá and Santarém.
One-city leftover UFs PB, MA, AL, MS, MT, RN, AC, AP, and RR still have no leftover mid-size MUNICIPIO DE row with homologado and ITEM in that 2024 COMPRA file.
Divinópolis is the leftover municipal MG row with landed volume after those leftover one-city UFs still had no mid-size municipal row.
Petrópolis is the leftover municipal RJ row with landed volume after those leftover one-city UFs still had no mid-size municipal row.
Ipatinga is the leftover municipal MG row with landed volume after those leftover one-city UFs still had no mid-size municipal row.
Macaé is the leftover municipal RJ row with landed volume after those leftover one-city UFs still had no mid-size municipal row.
Santa Luzia is the leftover municipal MG row with landed volume after those leftover one-city UFs still had no mid-size municipal row.
Nova Friburgo is the leftover municipal RJ row with landed volume after those leftover one-city UFs still had no mid-size municipal row.
São Carlos, SP, IBGE 3548906, has 82 municipal rows, all from the Câmara.
Presidente Prudente, SP, IBGE 3541406, has 14 municipal rows from a pension institute, a foundation, and a health autarchy, and no MUNICIPIO DE PRESIDENTE PRUDENTE row.
One-city leftover UFs PB, MA, AL, MS, MT, RN, AC, AP, and RR still have no leftover mid-size MUNICIPIO DE row with homologado and ITEM in that 2024 COMPRA file.
Marília is the leftover municipal SP row with landed volume after those leftover one-city UFs still had no mid-size municipal row and São Carlos had only Câmara rows.
Balneário Camboriú is the leftover municipal SC row with landed volume after those leftover one-city UFs still had no mid-size municipal row.
Rio Largo, AL, IBGE 2707701, has 129 municipal rows from MUNICIPIO DE RIO LARGO, but the 2022 population sits below the 100k-500k band.
Cáceres, MT, IBGE 5102504, has 36 municipal rows from MUNICIPIO DE CACERES, but the 2022 population sits below the 100k-500k band.
Pato Branco, PR, IBGE 4118501, has 85 municipal rows from MUNICIPIO DE PATO BRANCO, but the 2022 population sits below the 100k-500k band.
Francisco Beltrão, PR, IBGE 4108403, has 159 municipal rows from MUNICIPIO DE FRANCISCO BELTRAO, but the 2022 population sits below the 100k-500k band.
Resende, RJ, IBGE 3304201, has 27 municipal rows, all from the Câmara.
Barra Mansa, RJ, IBGE 3300407, has no municipal row in that 2024 COMPRA file.
Patos de Minas, MG, IBGE 3148004, has no municipal row in that 2024 COMPRA file.
Poços de Caldas, MG, IBGE 3151800, has no municipal row in that 2024 COMPRA file.
Guarapuava, PR, IBGE 4109401, has 33 municipal rows, all from the urban services company, and no MUNICIPIO DE GUARAPUAVA row.
Toledo, PR, IBGE 4127700, has 7 municipal rows, all from the Câmara.
Cariacica, ES, IBGE 3201308, has 4 municipal rows from MUNICIPIO DE CARIACICA and 1 with valor_total_homologado, but that homologado compra has no ITEM row in the 2024 ITEM file.
The 2024 COMPRA file has 57,384 municipal rows across 731 distinct municipio names.
Volta Redonda has 964 municipal contratacoes (959 unique id_compra), the highest volume among clearly mid-size non-capital cities after excluding Uberlandia / Ribeirao Preto which sit above 500k.
Other candidates present with volume: Bauru 736, Caxias do Sul 577, Maringa 425, Taubate 384, Joinville 346, Cascavel 245, Campina Grande 225 municipal 2024, Londrina 257, Niteroi 238, Santa Maria 240, Juiz de Fora 142, Foz do Iguacu 871, Montes Claros 67, Governador Valadares 78, Canoas 11, Lages 199, Santarem 23, Rio Verde 384, Paulo Afonso 63 municipal 46 homologado, Sao Lourenco da Mata 65 municipal 64 homologado, Crato 69 municipal 45 homologado, Ariquemes 222 municipal 183 homologado, Colatina 5 municipal 5 homologado, Castanhal 24 municipal 23 homologado, Divinopolis 332 municipal 288 homologado, Petropolis 19 municipal 19 homologado, Ipatinga 62 municipal 47 homologado, Macae 182 municipal 160 homologado, Santa Luzia 65 municipal 58 homologado, Nova Friburgo 154 municipal 130 homologado, Marilia 95 municipal 82 homologado, Balneario Camboriu 74 municipal 69 homologado.

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
