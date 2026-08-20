from __future__ import annotations

from pathlib import Path

import polars as pl

from compras_ingest.cpf import mask_frame
from compras_ingest.ids import record_hash
from compras_ingest.landing import LandingRef, LandingStore, partition_date_of
from compras_ingest.settings import Settings
from compras_ingest.csvio import read_csv
from compras_normalize.text import fold, parse_datetime


def load_compras_gov(settings: Settings, compra_path: Path | None = None, item_path: Path | None = None) -> pl.DataFrame:
    compra_p, item_p = _resolve_paths(settings, compra_path, item_path)
    compra = mask_frame(read_csv(compra_p))
    item = mask_frame(read_csv(item_p))
    return _join(compra, item)


def land_compras_gov(settings: Settings, store: LandingStore | None = None) -> tuple[LandingRef, pl.DataFrame]:
    store = store or LandingStore(settings)
    raw = load_compras_gov(settings)
    hashed = _with_record_hash(raw)
    dates = [parse_datetime(v) for v in hashed["datapublicacaopncp"].to_list()] if "datapublicacaopncp" in hashed.columns else []
    part = partition_date_of(dates)
    ref = store.write_parquet("compras_gov", part, hashed)
    return ref, hashed


def _resolve_paths(settings: Settings, compra_path: Path | None, item_path: Path | None) -> tuple[Path, Path]:
    if compra_path and item_path:
        return compra_path, item_path
    directory = settings.compras_gov_dir
    if directory is None:
        raise FileNotFoundError("COMPRAS_GOV_DIR missing and download is not used in this slice")
    compra = _find(directory, kind="compra")
    item = _find(directory, kind="item")
    return compra, item


def _find(directory: Path, kind: str) -> Path:
    csvs = list(directory.glob("*.csv"))
    if kind == "item":
        for p in csvs:
            if "item" in p.name.lower():
                return p
    else:
        for p in csvs:
            if "compra" in p.name.lower() and "item" not in p.name.lower():
                return p
    raise FileNotFoundError(f"no {kind} CSV in {directory}")


def _join(compra: pl.DataFrame, item: pl.DataFrame) -> pl.DataFrame:
    compra_n = _lower_cols(compra)
    item_n = _lower_cols(item)
    key = "idcompra"
    if key not in compra_n.columns or key not in item_n.columns:
        raise ValueError("compras_gov CSVs need idCompra on both files")
    overlap = [c for c in compra_n.columns if c in item_n.columns and c != key]
    compra_keep = compra_n.rename({c: f"compra_{c}" for c in overlap})
    joined = item_n.join(compra_keep, on=key, how="left")
    return joined.with_columns(pl.lit("compras_gov").alias("source"))


def _with_record_hash(df: pl.DataFrame) -> pl.DataFrame:
    rec_ids = []
    hashes = []
    for row in df.iter_rows(named=True):
        folded = {fold(k).replace(" ", "").replace("_", ""): v for k, v in row.items()}
        rec = str(folded.get("idcompraitem") or f"{folded.get('idcompra')}:{folded.get('numeroitemcompra')}")
        payload = {
            k: row[k]
            for k in sorted(row)
            if fold(k) not in {"record_hash", "record_id", "source"}
        }
        rec_ids.append(rec)
        hashes.append(record_hash(payload))
    return df.with_columns(
        pl.Series("record_id", rec_ids),
        pl.Series("record_hash", hashes),
    )


def _lower_cols(df: pl.DataFrame) -> pl.DataFrame:
    return df.rename({c: fold(c).replace(" ", "").replace("_", "") for c in df.columns})
