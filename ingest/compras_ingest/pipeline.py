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
    catalog_ref, _catalog_df = land_catalogo_cnbs(settings, store)
    receita_ref: dict = {"source": "receita_cnpj", "skipped": True}
    if settings.receita_cnpj_path is not None:
        landed_cnpj, _cnpj_df = land_receita_cnpj(settings, store)
        receita_ref = landed_cnpj.as_dict()
    landing, raw = land_compras_gov(settings, store)
    compras_ids = set()
    if "numerocontrolepncp" in raw.columns:
        compras_ids = {str(v) for v in raw["numerocontrolepncp"].to_list() if v}
    ocds_report = {}
    if settings.ocds_path is not None:
        _, ocds_report = land_ocds(settings, compras_ids, store)
    items, warehouse = warehouse_from_landing(
        settings,
        store,
        landing.as_dict(),
        catalog_ref.as_dict(),
        receita_ref,
    )
    flags, flag_rows = run_tier1_and_write_flags(settings, store, items)
    return PipelineResult(
        landing,
        ocds_report,
        warehouse["entities"],
        warehouse["facts"],
        flag_rows,
        items,
        flags,
    )


def warehouse_from_landing(
    settings: Settings,
    store: LandingStore,
    compras: dict,
    catalog: dict,
    receita: dict | None = None,
) -> tuple[pl.DataFrame, dict]:
    """Normalize landed parquet and write warehouse rows. Does not land or detect."""
    apply_schema(settings)
    raw = store.read_parquet(_require_key(compras, "compras_gov"))
    catalog_df = store.read_parquet(_require_key(catalog, "catalogo_cnbs"))
    catalog_model = load_catalog([catalog_df])
    units = load_unit_table()
    cnpj_df = _read_optional_landing(store, receita)
    snapshot_id = str(compras.get("sha256") or "")
    if not snapshot_id:
        raise ValueError("compras_gov landing missing sha256")
    items = normalize_frame(
        raw,
        catalog_model,
        units,
        cnpj_df,
        snapshot_id,
        settings.methodology_version,
    )
    entity_counts = write_entities(settings, items)
    fact_rows = write_facts(settings, items)
    part = str(compras.get("partition_date") or "")
    if not part:
        from datetime import datetime, timezone

        part = datetime.now(timezone.utc).date().isoformat()
    items_ref = store.write_parquet("normalized_items", part, items)
    return items, {
        "landing": {
            "source": compras.get("source"),
            "sha256": snapshot_id,
            "key": compras.get("key"),
            "uri": compras.get("uri"),
            "partition_date": compras.get("partition_date"),
        },
        "entities": entity_counts,
        "facts": fact_rows,
        "items_key": items_ref.key,
        "snapshot_id": snapshot_id,
    }


def run_tier1_and_write_flags(
    settings: Settings,
    store: LandingStore,
    items: pl.DataFrame,
) -> tuple[pl.DataFrame, int]:
    """Run internal Tier 1 detectors and persist flags. Does not land or normalize."""
    sanctions = _load_sanctions(settings)
    landing_records = _collect_landing_records(store, "compras_gov")
    flags = run_tier1(items, landing_records=landing_records, sanctions=sanctions)
    return flags, write_flags(settings, flags, items)


def _require_key(ref: dict | None, name: str) -> str:
    if not ref or ref.get("skipped"):
        raise ValueError(f"{name} landing was skipped or missing")
    key = ref.get("key")
    if not key:
        raise ValueError(f"{name} landing missing key")
    return str(key)


def _read_optional_landing(store: LandingStore, ref: dict | None) -> pl.DataFrame | None:
    if not ref or ref.get("skipped") or not ref.get("key"):
        return None
    df = store.read_parquet(str(ref["key"]))
    return None if df.is_empty() else df


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
