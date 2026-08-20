from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl

from compras_detect.tier1 import run_tier1
from compras_ingest.csvio import read_csv
from compras_ingest.landing import LandingRef, LandingStore
from compras_ingest.settings import Settings
from compras_ingest.sources.catalogo_cnbs import land_catalogo_cnbs
from compras_ingest.sources.compras_gov import land_compras_gov
from compras_ingest.sources.ocds import land_ocds
from compras_ingest.sources.receita_cnpj import land_receita_cnpj
from compras_ingest.warehouse import apply_schema, write_entities, write_facts, write_flags
from compras_normalize.catalog import load_catalog
from compras_normalize.items import normalize_frame
from compras_normalize.units import load_unit_table


@dataclass
class PipelineResult:
    landing: LandingRef
    ocds_report: dict
    entity_counts: dict[str, int]
    fact_rows: int
    flag_rows: int
    items: pl.DataFrame = field(repr=False)
    flags: pl.DataFrame = field(repr=False)


def run_compras_slice(settings: Settings, store: LandingStore | None = None) -> PipelineResult:
    store = store or LandingStore(settings)
    apply_schema(settings)
    catalog_ref, catalog_df = land_catalogo_cnbs(settings, store)
    _ = catalog_ref
    cnpj_df = pl.DataFrame()
    if settings.receita_cnpj_path is not None:
        _, cnpj_df = land_receita_cnpj(settings, store)
    landing, raw = land_compras_gov(settings, store)
    compras_ids = set()
    if "numerocontrolepncp" in raw.columns:
        compras_ids = {str(v) for v in raw["numerocontrolepncp"].to_list() if v}
    ocds_report = {}
    if settings.ocds_path is not None:
        _, ocds_report = land_ocds(settings, compras_ids, store)
    frames = [catalog_df]
    if settings.catalogo_cnbs_dir is not None:
        frames = [read_csv(p) for p in sorted(settings.catalogo_cnbs_dir.glob("*.csv"))]
    catalog = load_catalog(frames)
    units = load_unit_table()
    items = normalize_frame(
        raw,
        catalog,
        units,
        cnpj_df if not cnpj_df.is_empty() else None,
        landing.sha256,
        settings.methodology_version,
    )
    entity_counts = write_entities(settings, items)
    fact_rows = write_facts(settings, items)
    sanctions = _load_sanctions(settings)
    landing_records = _collect_landing_records(store, "compras_gov")
    flags = run_tier1(items, landing_records=landing_records, sanctions=sanctions)
    flag_rows = write_flags(settings, flags, items)
    return PipelineResult(landing, ocds_report, entity_counts, fact_rows, flag_rows, items, flags)


def _load_sanctions(settings: Settings) -> pl.DataFrame | None:
    directory = settings.sanctions_dir
    if directory is None:
        return None
    frames = [read_csv(p) for p in sorted(directory.glob("*.csv"))]
    if not frames:
        return None
    return pl.concat(frames, how="diagonal_relaxed")


def _collect_landing_records(store: LandingStore, source: str) -> pl.DataFrame:
    keys = store.list_parquet(source)
    if not keys:
        return pl.DataFrame()
    frames = []
    for key in keys:
        df = store.read_parquet(key)
        keep = [c for c in ("record_id", "record_hash", "numerocontrolepncp") if c in df.columns]
        if "record_id" not in keep:
            continue
        slim = df.select(keep)
        if "pncp_id" not in slim.columns and "numerocontrolepncp" in slim.columns:
            slim = slim.rename({"numerocontrolepncp": "pncp_id"})
        frames.append(slim)
    return pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()


def land_second_snapshot(settings: Settings, mutate_record_id: str, store: LandingStore | None = None) -> LandingRef:
    """Second landing of the same source with one field changed. Exercises retroactive_edit."""
    from compras_ingest.sources.compras_gov import load_compras_gov, _with_record_hash
    from compras_ingest.landing import partition_date_of
    from compras_normalize.text import parse_datetime

    store = store or LandingStore(settings)
    raw = _with_record_hash(load_compras_gov(settings))
    if "objetocompra" in raw.columns:
        raw = raw.with_columns(
            pl.when(pl.col("record_id") == mutate_record_id)
            .then(pl.col("objetocompra") + pl.lit(" [edit]"))
            .otherwise(pl.col("objetocompra"))
            .alias("objetocompra")
        )
        raw = _with_record_hash(raw.drop(["record_id", "record_hash"]))
    dates = [parse_datetime(v) for v in raw["datapublicacaopncp"].to_list()] if "datapublicacaopncp" in raw.columns else []
    part = partition_date_of(dates)
    # Force a later partition so both hashes remain.
    later = part
    if later.endswith("15"):
        later = later[:-2] + "16"
    else:
        later = part[:8] + "28"
    return store.write_parquet("compras_gov", later, raw)
