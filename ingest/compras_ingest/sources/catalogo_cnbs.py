from __future__ import annotations

from pathlib import Path

import polars as pl

from compras_ingest.csvio import read_csv
from compras_ingest.landing import LandingRef, LandingStore
from compras_ingest.settings import Settings
from compras_normalize.catalog import load_catalog
from compras_normalize.text import fold


def land_catalogo_cnbs(settings: Settings, store: LandingStore | None = None) -> tuple[LandingRef, pl.DataFrame]:
    store = store or LandingStore(settings)
    directory = settings.catalogo_cnbs_dir
    if directory is None:
        raise FileNotFoundError("CATALOGO_CNBS_DIR missing")
    frames = [read_csv(p) for p in sorted(directory.glob("*.csv"))]
    if not frames:
        raise FileNotFoundError(f"no catalog CSV in {directory}")
    # Validate shape via catalog loader.
    load_catalog(frames)
    tagged = []
    for frame, path in zip(frames, sorted(directory.glob("*.csv")), strict=True):
        tipo = "S" if "catser" in path.name.lower() or "servico" in path.name.lower() else "M"
        cols = {fold(c).replace(" ", ""): c for c in frame.columns}
        tipo_col = cols.get("tipo")
        if tipo_col is None:
            frame = frame.with_columns(pl.lit(tipo).alias("tipo"))
        tagged.append(frame)
    df = pl.concat(tagged, how="diagonal_relaxed")
    from datetime import datetime, timezone

    part = datetime.now(timezone.utc).date().isoformat()
    ref = store.write_parquet("catalogo_cnbs", part, df)
    return ref, df


def catalog_frames_from_dir(directory: Path) -> list[pl.DataFrame]:
    return [read_csv(p) for p in sorted(directory.glob("*.csv"))]
