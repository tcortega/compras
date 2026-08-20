from __future__ import annotations

from datetime import date, timedelta

from compras_ingest.landing import LandingRef, LandingStore
from compras_ingest.settings import Settings, TRAILING_WINDOW_DAYS
from compras_ingest.sources.cgu_ceis_cnep import land_cgu_ceis_cnep
from compras_ingest.sources.compras_gov import land_compras_gov
from compras_ingest.sources.pncp_consulta import land_pncp_consulta
from compras_ingest.sources.tce_rs_licitacon import land_tce_rs_licitacon
from compras_ingest.sources.tce_sp_licitacao import land_tce_sp_licitacao

REFETCH_SOURCES = (
    "compras_gov",
    "pncp_consulta",
    "tce_sp_licitacao",
    "tce_rs_licitacon",
    "cgu_ceis_cnep",
)
SCHEDULE_NAME = "trailing_window_refetch_daily"
JOB_NAME = "trailing_window_refetch"
SCHEDULE_CRON = "0 3 * * *"
SCHEDULE_TZ = "America/Sao_Paulo"


def trailing_window_days(settings: Settings) -> int:
    return int(settings.trailing_window_days or TRAILING_WINDOW_DAYS)


def trailing_window(settings: Settings, as_of: date | None = None) -> tuple[date, date]:
    days = trailing_window_days(settings)
    end = as_of or settings.trailing_window_as_of or date.today()
    return end - timedelta(days=days), end


def refetch_source(
    settings: Settings,
    source: str,
    store: LandingStore | None = None,
    window: tuple[date, date] | None = None,
) -> LandingRef:
    store = store or LandingStore(settings)
    window = window or trailing_window(settings)
    if source == "compras_gov":
        ref, _ = land_compras_gov(settings, store)
        return ref
    if source == "pncp_consulta":
        ref, _, _ = land_pncp_consulta(settings, store, window=window)
        return ref
    if source == "tce_sp_licitacao":
        ref, _ = land_tce_sp_licitacao(settings, store)
        return ref
    if source == "tce_rs_licitacon":
        ref, _ = land_tce_rs_licitacon(settings, store)
        return ref
    if source == "cgu_ceis_cnep":
        ref, _ = land_cgu_ceis_cnep(settings, store)
        return ref
    raise ValueError(f"unknown refetch source {source}")


def refetch_trailing_window(
    settings: Settings,
    store: LandingStore | None = None,
) -> dict[str, dict]:
    store = store or LandingStore(settings)
    window = trailing_window(settings)
    out: dict[str, dict] = {}
    for source in REFETCH_SOURCES:
        ref = refetch_source(settings, source, store, window)
        out[source] = {
            **ref.as_dict(),
            "trailing_window_days": trailing_window_days(settings),
            "window_start": window[0].isoformat(),
            "window_end": window[1].isoformat(),
        }
    return out
