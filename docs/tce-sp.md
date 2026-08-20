# TCE-SP monthly licitacao ingest

Internal only.
The explorer does not read this landing.
Participant proposal values do not appear on public routes.

Source: monthly LICITACOES ZIP resolved from https://transparencia.tce.sp.gov.br/conjunto-de-dados
Host allowlist: transparencia.tce.sp.gov.br
The cubo SQL dump is not used.
That cube has awarded contractor and contract value, not losing bids.

Slice: Município Bauru, IBGE 3506003, UF SP.
The monthly CSV has no IBGE column.
Rows are kept when folded Município equals bauru.

Files are streamed from ZIP then CSV.
A full month is never loaded into memory.

CPF is masked at ingest as `***.XXX.XXX-**`.
CNPJ is stored.
Valor da Proposta includes classified losers and winners.

CI uses `ingest/fixtures/tce_sp_licitacao/licitacao.csv`.
Live download is `TCE_SP_FETCH=1`.
