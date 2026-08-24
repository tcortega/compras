from __future__ import annotations

# Cadence locked from official URL shape / portal text. Do not guess.

# compras_gov daily: live index has diario/YYYY/MM/DD COMPRA+ITEM.
# Trailing day uses that pair when both exist, else mensal/YYYY/MM.
# Stream-filter stays the covered IBGE set. Years 2024,2025,2026 stay D1.
DAILY_COMPRAS_GOV_REASON = (
    "official diario/YYYY/MM/DD COMPRA+ITEM exists; else mensal/YYYY/MM"
)

# pncp_consulta daily: consulta API can be polled daily. D4 owns the cursor.
DAILY_PNCP_REASON = "PNCP consulta API is pollable daily; this schedule only rematerializes the land asset"

# cgu_ceis_cnep daily: Portal listing is /download-de-dados/{ceis|cnep}/YYYYMMDD.
DAILY_CGU_REASON = "CGU CEIS/CNEP official listing is a dated YYYYMMDD zip"

# ocds daily: BUILD_SPEC and OCP publication 157 feed are daily.
DAILY_OCDS_REASON = "OCP publication 157 jsonl feed is daily"

# tce_rs daily: portal text, current and previous year update daily.
DAILY_TCE_RS_REASON = "TCE-RS licitacoes-consolidado current and previous year update daily"

# tce_sp monthly: official zip is licitacao-YYYY-MM. Fase IV cube is monthly.
MONTHLY_TCE_SP_REASON = "TCE-SP licitacao zip is year-month; listing cadence is esporadica"

# receita_cnpj monthly: RFB share is YYYY-MM folders.
MONTHLY_RECEITA_REASON = "RFB CNPJ dump is published as YYYY-MM folders"

# catalogo_cnbs monthly: catalog dump is not a daily feed.
MONTHLY_CATALOGO_REASON = "CATMAT/CATSER catalog dump is monthly, not a daily extract"

SCHEDULE_TZ = "America/Sao_Paulo"
DAILY_SCHEDULE_NAME = "incremental_land_daily"
DAILY_JOB_NAME = "incremental_land_daily"
DAILY_CRON = "0 4 * * *"
MONTHLY_SCHEDULE_NAME = "incremental_land_monthly"
MONTHLY_JOB_NAME = "incremental_land_monthly"
MONTHLY_CRON = "0 5 1 * *"

# Asset keys selected by the daily incremental job.
DAILY_ASSET_KEYS = (
    "compras_gov",
    "ocds_crosscheck",
    "pncp_consulta",
    "tce_rs_licitacon",
    "cgu_ceis_cnep",
)

# Asset keys selected by the monthly incremental job.
MONTHLY_ASSET_KEYS = (
    "catalogo_cnbs",
    "receita_cnpj",
    "tce_sp_licitacao",
)
