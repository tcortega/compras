# TCE-RS LicitaCon ingest

Internal only.
The explorer does not read this landing.
Participant rows persist in internal warehouse table `licitacao_participante`.
The explorer does not read that table.
Participant proposal values do not appear on public routes.

Source: annual licitacoes-consolidado ZIP from https://dados.tce.rs.gov.br/
CKAN package: https://dados.tce.rs.gov.br/api/3/action/package_show?id=licitacoes-consolidado-2025
Official leiaute: https://tcers.tc.br/repo/cex/licitacon/cpt/eValidador_LicitaCon_Manual_Leiaute_1.4.pdf
Official example remessa: https://tcers.tc.br/repo/cex/licitacon/cpt/eValidador-licitacon-exemplos-1.4.zip
Host allowlist: dados.tce.rs.gov.br and tcers.tc.br.
No third-party mirrors.

dados.tce.rs.gov.br TLS has failed with unexpected EOF from some hosts.
Ingest retries a few times.
If the live CKAN ZIP still fails, CI and the default run use the official example remessa plus a small fixture.

Slice for live fetch: Caxias do Sul, RS, IBGE 4305108.
Open data adds CD_ORGAO.
Rows are kept when that column matches the slice orgao.
Example remessa orgao 89550032000174 is used for fixtures.

Tables landed: LICITANTE, PROPOSTA, LOTE_PROPOSTA, ITEM_PROPOSTA, plus LICITACAO, LOTE, and ITEM keys for NR_DOCUMENTO_VENCEDOR.
PESSOAS, COMISSAO, DOTACAO, EVENTO, and DOCUMENTO are skipped.

Files are streamed from ZIP then CSV or remessa TXT.
A full year is never loaded into memory.

CPF is masked at ingest as `***.XXX.XXX-**` when TP_DOCUMENTO_LICITANTE is F, and on representative CPF fields.
CNPJ is stored.
Proposal values include classified losers and winners.

CI and compose seed use `ingest/fixtures/tce_rs_licitacon/` with `TCE_RS_FETCH=0`.
Fixture mode does not contact dados.tce.rs.gov.br or tcers.tc.br.
Live CKAN download is `TCE_RS_FETCH=1`.
