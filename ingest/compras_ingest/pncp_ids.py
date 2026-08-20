from __future__ import annotations

from pathlib import Path

import polars as pl

from compras_ingest.landing import LandingStore
from compras_ingest.slice import SLICE_IBGE_CODES, SLICE_IBGE_UF, ibge_token

_PNCP_COLS = ("numerocontrolepncp", "idcontratacaopncp", "numero_controle_pncp", "pncp_id")
_ITEM_COLS = ("numeroitem", "numero_item", "numeroitemcompra")


def compra_identity(pncp_id: object) -> tuple[str, int, int] | None:
    """Map consulta `{cnpj}-1-{seq}/{ano}` and bulk `{cnpj}-1-{ano}-{seq}` to one key."""
    raw = str(pncp_id or "").strip()
    if not raw:
        return None
    if "/" in raw:
        head, year = raw.rsplit("/", 1)
        parts = head.split("-")
        if len(parts) >= 3 and year.isdigit() and parts[-1].isdigit():
            cnpj = "".join(c for c in parts[0] if c.isdigit())
            if len(cnpj) == 14:
                return cnpj, int(year), int(parts[-1])
        return None
    parts = raw.split("-")
    if len(parts) >= 4 and parts[-2].isdigit() and parts[-1].isdigit():
        cnpj = "".join(c for c in parts[0] if c.isdigit())
        if len(cnpj) == 14:
            return cnpj, int(parts[-2]), int(parts[-1])
    return None


def item_identity(pncp_id: object, numero_item: object) -> tuple[str, int, int, int] | None:
    compra = compra_identity(pncp_id)
    if compra is None:
        return None
    raw = str(numero_item or "").strip()
    if not raw or not raw.lstrip("-").isdigit():
        return None
    return (*compra, int(raw))


def live_ibge_targets() -> list[tuple[str, str]]:
    """59 covered municipios only. Never Brazil."""
    return sorted(SLICE_IBGE_UF.items())


def fixture_ibge_targets(ibge: str, uf: str) -> list[tuple[str, str]]:
    token = ibge_token(ibge)
    if token not in SLICE_IBGE_CODES:
        raise RuntimeError(f"pncp_consulta ibge {ibge} is outside the 59")
    return [(token, str(uf or SLICE_IBGE_UF[token]).upper())]


def complete_compra_keys(store: LandingStore) -> set[tuple[str, int, int]]:
    """Compras.gov ITEM rows already cover this compra. Skip detail fetch."""
    keys: set[tuple[str, int, int]] = set()
    for parquet in store.list_parquet("compras_gov"):
        df = store.read_parquet(parquet)
        if df.is_empty():
            continue
        col = _first_col(df, *_PNCP_COLS)
        if col is None:
            continue
        for value in df[col].to_list():
            ident = compra_identity(value)
            if ident:
                keys.add(ident)
    return keys


def complete_item_keys(store: LandingStore) -> set[tuple[str, int, int, int]]:
    keys: set[tuple[str, int, int, int]] = set()
    for parquet in store.list_parquet("compras_gov"):
        df = store.read_parquet(parquet)
        if df.is_empty():
            continue
        pncp_col = _first_col(df, *_PNCP_COLS)
        item_col = _first_col(df, *_ITEM_COLS)
        if pncp_col is None:
            continue
        items = df[item_col].to_list() if item_col else [None] * df.height
        for pncp_id, numero in zip(df[pncp_col].to_list(), items, strict=True):
            ident = item_identity(pncp_id, numero)
            if ident:
                keys.add(ident)
    return keys


def is_complete_compra(pncp_id: object, covered: set[tuple[str, int, int]]) -> bool:
    ident = compra_identity(pncp_id)
    return ident is not None and ident in covered


def pncp_gap_rows(df: pl.DataFrame, covered: set[tuple[str, int, int]]) -> pl.DataFrame:
    if df.is_empty():
        return df
    col = _first_col(df, *_PNCP_COLS)
    if col is None:
        return df
    keep = []
    for row in df.iter_rows(named=True):
        keep.append(not is_complete_compra(row.get(col), covered))
    if not any(keep):
        return df.head(0)
    return df.filter(pl.Series("keep", keep))


def _first_col(df: pl.DataFrame, *names: str) -> str | None:
    folded = {c.lower().replace("_", ""): c for c in df.columns}
    for name in names:
        key = name.lower().replace("_", "")
        if key in folded:
            return folded[key]
    return None


def parquet_sha(key: str) -> str:
    return Path(key).stem
