from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import polars as pl

from compras_detect.adjacency import build_adjacencies
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
from compras_ingest.pncp_ids import complete_compra_keys, parquet_sha, pncp_gap_rows
from compras_ingest.sources.pncp_consulta import land_pncp_consulta, land_pncp_consulta_gaps
from compras_ingest.sources.cgu_ceis_cnep import land_cgu_ceis_cnep, load_landed_sanctions
from compras_ingest.sources.receita_cnpj import cnpj_basicos_from_frame, land_receita_cnpj
from compras_ingest.sources.tce_rs_licitacon import land_tce_rs_licitacon
from compras_ingest.sources.tce_sp_licitacao import land_tce_sp_licitacao
from compras_ingest.ids import item_id
from compras_ingest.warehouse import (
    apply_schema,
    fetch_all_items,
    write_adjacencies,
    write_catalog,
    write_cnaes,
    write_entities,
    write_exclusions,
    write_facts,
    write_flags,
    write_fornecedor_socios,
    write_landing_sources,
)
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
    adjacency_rows: int
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
    pncp_ref, _, _ = land_pncp_consulta(settings, store)
    land_tce_sp_licitacao(settings, store)
    land_tce_rs_licitacon(settings, store)
    land_cgu_ceis_cnep(settings, store)
    items, warehouse = warehouse_from_landing(
        settings,
        store,
        landing.as_dict(),
        catalog_ref.as_dict(),
        receita_ref,
        pncp_ref.as_dict(),
    )
    flags, flag_rows = run_tier1_and_write_flags(settings, store, items)
    _, adjacency_rows = run_adjacency_and_write(settings, store)
    return PipelineResult(
        landing,
        ocds_report,
        warehouse["entities"],
        warehouse["facts"],
        flag_rows,
        warehouse.get("exclusions") or 0,
        adjacency_rows,
        items,
        flags,
    )


def warehouse_from_landing(
    settings: Settings,
    store: LandingStore,
    compras: dict,
    catalog: dict,
    receita: dict | None = None,
    pncp: dict | None = None,
) -> tuple[pl.DataFrame, dict]:
    """Normalize landed parquet, write warehouse rows, persist data-error exclusions. Does not land or run B-track detectors."""
    apply_schema(settings)
    year_keys = _compras_gov_keys(store, compras)
    catalog_df = store.read_parquet(_require_key(catalog, "catalogo_cnbs"))
    catalog_model = load_catalog([catalog_df])
    units = load_unit_table()
    cnpj_df = _read_optional_landing(store, receita)
    snapshot_id = str(compras.get("sha256") or "")
    item_frames: list[pl.DataFrame] = []
    for key in year_keys:
        raw = store.read_parquet(key)
        sha = Path(key).stem
        if not snapshot_id:
            snapshot_id = sha
        item_frames.append(
            normalize_frame(
                raw,
                catalog_model,
                units,
                cnpj_df,
                sha,
                settings.methodology_version,
            )
        )
    if not snapshot_id:
        raise ValueError("compras_gov landing missing sha256")
    items = pl.concat(item_frames, how="diagonal_relaxed") if item_frames else pl.DataFrame()
    gap_items, gap_n = _normalize_pncp_gaps(
        settings,
        store,
        catalog_model,
        units,
        cnpj_df,
        pncp,
    )
    if gap_items.height:
        items = pl.concat([items, gap_items], how="diagonal_relaxed") if items.height else gap_items
    entity_counts = write_entities(settings, items)
    entity_counts["cnae"] = write_cnaes(settings, _concat_source(store, "receita_cnpj_cnaes"))
    entity_counts["fornecedor_socio"] = write_fornecedor_socios(
        settings,
        _concat_source(store, "receita_cnpj_socios"),
        _concat_source(store, "receita_cnpj_qualificacoes"),
    )
    fact_rows = write_facts(settings, items)
    catalog_rows = write_catalog(settings, catalog_df)
    landing_sources = write_landing_sources(settings, store)
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
        "catalog": catalog_rows,
        "landing_sources": landing_sources,
        "exclusions": exclusion_rows,
        "anomaly_pool_n": pool.height,
        "anomaly_pool_key": pool_ref.key,
        "items_key": items_ref.key,
        "snapshot_id": snapshot_id,
        "pncp_gaps": gap_n,
    }


def run_pncp_consulta_gaps(
    settings: Settings,
    store: LandingStore | None = None,
    official=None,
    transport=None,
    sleeper=None,
    clock=None,
) -> tuple[LandingRef, pl.DataFrame, dict]:
    """Land PNCP gaps for the 59, write only those rows. Skip complete compras.gov compras."""
    store = store or LandingStore(settings)
    covered = complete_compra_keys(store)
    ref, raw, report = land_pncp_consulta_gaps(
        settings,
        store,
        official=official,
        transport=transport,
        sleeper=sleeper,
        clock=clock,
        covered=covered,
    )
    apply_schema(settings)
    catalog_ref, catalog_df = land_catalogo_cnbs(settings, store)
    catalog_model = load_catalog([catalog_df])
    units = load_unit_table()
    receita_keys = store.list_parquet("receita_cnpj")
    cnpj_df = store.read_parquet(receita_keys[-1]) if receita_keys else None
    gap_items, gap_n = _normalize_pncp_gaps(
        settings,
        store,
        catalog_model,
        units,
        cnpj_df if cnpj_df is not None and cnpj_df.height else None,
        ref.as_dict(),
    )
    entity_counts = write_entities(settings, gap_items) if gap_items.height else {}
    fresh = _new_items(settings, gap_items)
    fact_rows = write_facts(settings, fresh) if fresh.height else 0
    write_landing_sources(settings, store)
    _ = catalog_ref
    return ref, raw, {
        **report,
        "pncp_gaps": gap_n,
        "entities": entity_counts,
        "facts": fact_rows,
    }


def _normalize_pncp_gaps(
    settings: Settings,
    store: LandingStore,
    catalog_model,
    units,
    cnpj_df,
    pncp: dict | None,
) -> tuple[pl.DataFrame, int]:
    covered = complete_compra_keys(store)
    keys = store.list_parquet("pncp_consulta")
    if not keys:
        return pl.DataFrame(), 0
    snap = str((pncp or {}).get("sha256") or "")
    frames: list[pl.DataFrame] = []
    seen: set[str] = set()
    for key in keys:
        raw = store.read_parquet(key)
        if raw.is_empty():
            continue
        gaps = pncp_gap_rows(raw, covered)
        if gaps.is_empty():
            continue
        digest = snap or parquet_sha(key)
        normalized = normalize_frame(
            gaps,
            catalog_model,
            units,
            cnpj_df,
            digest,
            settings.methodology_version,
        )
        if "record_id" in normalized.columns:
            keep = []
            for row in normalized.iter_rows(named=True):
                rid = str(row.get("record_id") or "")
                if rid and rid in seen:
                    keep.append(False)
                    continue
                if rid:
                    seen.add(rid)
                keep.append(True)
            normalized = normalized.filter(pl.Series("keep", keep))
        if normalized.height:
            frames.append(normalized)
    if not frames:
        return pl.DataFrame(), 0
    out = pl.concat(frames, how="diagonal_relaxed")
    return out, out.height


def _new_items(settings: Settings, items: pl.DataFrame) -> pl.DataFrame:
    if items.is_empty():
        return items
    have = {str(row["id"]) for row in fetch_all_items(settings)}
    keep = []
    for row in items.iter_rows(named=True):
        iid = item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or ""))
        keep.append(iid not in have)
    if not any(keep):
        return items.head(0)
    return items.filter(pl.Series("keep", keep))


def warehouse_data_error_fixture(settings: Settings) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Write golden data-error items, persist exclusions, return items/exclusions/pool."""
    apply_schema(settings)
    items = read_csv(fixture_items_path())
    write_entities(settings, items)
    exclusions = detect_data_errors(items)
    write_exclusions(settings, exclusions, items)
    return items, exclusions, anomaly_pool(items, exclusions)


def run_adjacency_and_write(
    settings: Settings,
    store: LandingStore,
) -> tuple[pl.DataFrame, int]:
    """Build Receita adjacency edges from landed frames and persist them. Does not call C#."""
    estab, socios, snapshot_id = _load_landed_receita(store)
    edges = build_adjacencies(estab, socios, snapshot_id, settings.methodology_version)
    return edges, write_adjacencies(settings, edges)


def _load_landed_receita(store: LandingStore) -> tuple[pl.DataFrame, pl.DataFrame, str]:
    estab = _concat_source(store, "receita_cnpj")
    socios = _concat_source(store, "receita_cnpj_socios")
    keys = sorted(store.list_parquet("receita_cnpj"))
    snapshot_id = Path(keys[-1]).stem if keys else ""
    return estab, socios, snapshot_id


def _concat_source(store: LandingStore, source: str) -> pl.DataFrame:
    frames = []
    for key in store.list_parquet(source):
        df = store.read_parquet(key)
        if not df.is_empty():
            frames.append(df)
    return pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()


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


def _compras_gov_keys(store: LandingStore, compras: dict) -> list[str]:
    year_keys = store.year_partition_keys("compras_gov")
    if year_keys:
        return year_keys
    return [_require_key(compras, "compras_gov")]


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
