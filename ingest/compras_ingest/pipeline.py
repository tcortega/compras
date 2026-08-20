from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import polars as pl

from compras_detect.data_error import (
    anomaly_pool,
    catalog_reference_prices,
    detect_data_errors,
    fixture_items_path,
)
from compras_detect.tier1 import run_tier1
from compras_ingest.csvio import read_csv
from compras_ingest.landing import LandingRef, LandingStore
from compras_ingest.settings import Settings
from compras_ingest.sources.catalogo_cnbs import land_catalogo_cnbs
from compras_ingest.sources.compras_gov import land_compras_gov
from compras_ingest.sources.ocds import land_ocds
from compras_ingest.sources.pncp_consulta import land_pncp_consulta
from compras_ingest.sources.cgu_ceis_cnep import land_cgu_ceis_cnep, load_landed_sanctions
from compras_ingest.sources.receita_cnpj import cnpj_basicos_from_frame, land_receita_cnpj
from compras_ingest.sources.tce_rs_licitacon import land_tce_rs_licitacon
from compras_ingest.sources.tce_sp_licitacao import land_tce_sp_licitacao
from compras_ingest.warehouse import apply_schema, write_entities, write_exclusions, write_facts, write_flags
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
    exclusion_rows: int
    items: pl.DataFrame = field(repr=False)
    flags: pl.DataFrame = field(repr=False)


def run_compras_slice(settings: Settings, store: LandingStore | None = None) -> PipelineResult:
    store = store or LandingStore(settings)
    catalog_ref, _catalog_df = land_catalogo_cnbs(settings, store)
    landing, raw = land_compras_gov(settings, store)
    compras_ids = set()
    if "numerocontrolepncp" in raw.columns:
        compras_ids = {str(v) for v in raw["numerocontrolepncp"].to_list() if v}
    landed_cnpj, _cnpj_df = land_receita_cnpj(settings, store, cnpj_basicos=cnpj_basicos_from_frame(raw))
    receita_ref = landed_cnpj.as_dict()
    _, ocds_report = land_ocds(settings, compras_ids, store)
    land_pncp_consulta(settings, store)
    land_tce_sp_licitacao(settings, store)
    land_tce_rs_licitacon(settings, store)
    land_cgu_ceis_cnep(settings, store)
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
        warehouse.get("exclusions") or 0,
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
    """Normalize landed parquet, write warehouse rows, persist data-error exclusions. Does not land or run B-track detectors."""
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
    catalog_prices = catalog_reference_prices(catalog_df)
    exclusions = detect_data_errors(items, catalog_prices=catalog_prices)
    exclusion_rows = write_exclusions(settings, exclusions, items)
    pool = anomaly_pool(items, exclusions)
    part = str(compras.get("partition_date") or "")
    if not part:
        from datetime import datetime, timezone

        part = datetime.now(timezone.utc).date().isoformat()
    items_ref = store.write_parquet("normalized_items", part, items)
    pool_ref = store.write_parquet("anomaly_pool", part, pool)
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
        "exclusions": exclusion_rows,
        "anomaly_pool_n": pool.height,
        "anomaly_pool_key": pool_ref.key,
        "items_key": items_ref.key,
        "snapshot_id": snapshot_id,
    }


def warehouse_data_error_fixture(settings: Settings) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Write golden data-error items, persist exclusions, return items/exclusions/pool."""
    apply_schema(settings)
    items = read_csv(fixture_items_path())
    write_entities(settings, items)
    exclusions = detect_data_errors(items)
    write_exclusions(settings, exclusions, items)
    return items, exclusions, anomaly_pool(items, exclusions)


def run_tier1_and_write_flags(
    settings: Settings,
    store: LandingStore,
    items: pl.DataFrame,
) -> tuple[pl.DataFrame, int]:
    """Run internal Tier 1 detectors and persist flags. Does not land or normalize."""
    sanctions = load_landed_sanctions(store)
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


def _collect_landing_records(store: LandingStore, source: str) -> pl.DataFrame:
    keys = store.list_parquet(source)
    if not keys:
        return pl.DataFrame()
    frames = []
    for key in keys:
        df = store.read_parquet(key)
        if "record_id" not in df.columns:
            continue
        digest = Path(key).stem
        part = _partition_date_from_key(key)
        extra = df.with_columns(
            pl.lit(digest).alias("_landing_sha256"),
            pl.lit(part).alias("_partition_date"),
        )
        if "snapshot_id" not in extra.columns:
            extra = extra.with_columns(pl.lit(digest).alias("snapshot_id"))
        if "pncp_id" not in extra.columns and "numerocontrolepncp" in extra.columns:
            extra = extra.rename({"numerocontrolepncp": "pncp_id"})
        frames.append(extra)
    return pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()


def land_second_snapshot(settings: Settings, mutate_record_id: str, store: LandingStore | None = None) -> LandingRef:
    """Second landing with planted watched-field edits. Exercises retroactive_edit."""
    from compras_ingest.sources.compras_gov import load_compras_gov, _with_record_hash

    _ = mutate_record_id
    store = store or LandingStore(settings)
    raw = _with_record_hash(load_compras_gov(settings))
    overlay = _load_retroactive_edit_snap2()
    raw = _overlay_item_snapshot(raw, overlay)
    drop = [c for c in ("record_id", "record_hash") if c in raw.columns]
    raw = _with_record_hash(raw.drop(drop) if drop else raw)
    later = _next_compras_partition(store)
    return store.write_parquet("compras_gov", later, raw)


def _load_retroactive_edit_snap2() -> pl.DataFrame:
    from compras_detect.tier1.retroactive_edit import fixture_dir
    from compras_ingest.csvio import read_csv

    path = fixture_dir() / "snap2.csv"
    if not path.exists():
        raise FileNotFoundError(f"retroactive_edit snap2 missing: {path}")
    return read_csv(path)


def _overlay_item_snapshot(raw: pl.DataFrame, snap2: pl.DataFrame) -> pl.DataFrame:
    from compras_ingest.sources.compras_gov import _lower_cols

    overlay = _lower_cols(snap2)
    key = "idcompraitem"
    if key not in overlay.columns:
        raise ValueError("retroactive_edit snap2 needs idCompraItem")
    by_id = {str(row[key]): row for row in overlay.iter_rows(named=True)}
    rows = []
    for row in raw.iter_rows(named=True):
        rid = str(row.get(key) or row.get("record_id") or "")
        if rid not in by_id:
            rows.append(row)
            continue
        updated = dict(row)
        for col, value in by_id[rid].items():
            if col in updated:
                updated[col] = value
        rows.append(updated)
    return pl.DataFrame(rows)


def _partition_date_from_key(key: str) -> str:
    for part in Path(key).parts:
        if part.startswith("date="):
            return part.split("=", 1)[1]
    return ""


def _next_compras_partition(store: LandingStore) -> str:
    found: list[date] = []
    for key in store.list_parquet("compras_gov"):
        raw = _partition_date_from_key(key)
        if not raw:
            continue
        try:
            found.append(date.fromisoformat(raw))
        except ValueError:
            continue
    if not found:
        return date.today().isoformat()
    return (max(found) + timedelta(days=1)).isoformat()
