"""Official anual COMPRA+ITEM backfill then warehouse write. Receita remote dump is a later pass."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from compras_ingest.landing import LandingStore
from compras_ingest.pipeline import warehouse_from_landing
from compras_ingest.settings import Settings
from compras_ingest.sources.catalogo_cnbs import land_catalogo_cnbs
from compras_ingest.sources.compras_gov import land_compras_gov
from compras_ingest.sources.ocds import land_ocds
from compras_ingest.sources.pncp_consulta import land_pncp_consulta
from compras_ingest.sources.receita_cnpj import cnpj_basicos_from_frame, land_receita_cnpj
from compras_ingest.sources.cgu_ceis_cnep import land_cgu_ceis_cnep
from compras_ingest.sources.tce_rs_licitacon import land_tce_rs_licitacon
from compras_ingest.sources.tce_sp_licitacao import land_tce_sp_licitacao
from compras_ingest.warehouse import fetch_counts, fetch_contratacao_anos


def main() -> int:
    settings = Settings.from_env()
    store = LandingStore(settings)
    print("fetch", {
        "COMPRAS_GOV_FETCH": settings.compras_gov_fetch,
        "RECEITA_CNPJ_FETCH": settings.receita_cnpj_fetch,
        "OCDS_FETCH": settings.ocds_fetch,
        "PNCP_CONSULTA_FETCH": settings.pncp_consulta_fetch,
        "TCE_SP_FETCH": settings.tce_sp_fetch,
        "TCE_RS_FETCH": settings.tce_rs_fetch,
        "SANCTIONS_FETCH": settings.sanctions_fetch,
        "YEARS": settings.compras_gov_years,
    }, flush=True)
    cat, _ = land_catalogo_cnbs(settings, store)
    landing, raw = land_compras_gov(settings, store)
    print("landed_compras_gov rows", raw.height, "sha", landing.sha256, flush=True)
    basicos = cnpj_basicos_from_frame(raw)
    print("cnpj_basicos", len(basicos), flush=True)
    del raw
    receita_ref, _ = land_receita_cnpj(settings, store, cnpj_basicos=basicos)
    print("receita", receita_ref.sha256, "rows", receita_ref.rows, flush=True)
    compras_ids: set[str] = set()
    ocds_ref, ocds_report = land_ocds(settings, compras_ids, store)
    print("ocds", ocds_report, flush=True)
    pncp_ref, pncp_df, pncp_report = land_pncp_consulta(settings, store)
    print("pncp", pncp_report, "rows", pncp_df.height, flush=True)
    tce_sp, _ = land_tce_sp_licitacao(settings, store)
    tce_rs, _ = land_tce_rs_licitacon(settings, store)
    cgu, _ = land_cgu_ceis_cnep(settings, store)
    print("tce_sp", tce_sp.sha256, "tce_rs", tce_rs.sha256, "cgu", cgu.sha256, flush=True)
    items, summary = warehouse_from_landing(
        settings,
        store,
        landing.as_dict(),
        cat.as_dict(),
        receita_ref.as_dict(),
        pncp_ref.as_dict(),
    )
    print("warehouse", summary, "items", items.height, flush=True)
    print("counts", fetch_counts(settings), flush=True)
    print("anos", fetch_contratacao_anos(settings), flush=True)
    print("ok", datetime.now(timezone.utc).isoformat(), datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
