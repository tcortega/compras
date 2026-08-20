from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from math import log10
from pathlib import Path

import polars as pl

from compras_detect.tier1.mismatch import detect_qty_price_mismatch
from compras_normalize.text import fold, parse_decimal

REASONS = (
    "qty_unit_price_neq_total",
    "decimal_shift",
    "qty_eq_1_collapse",
    "zero_or_negative",
    "duplicate_row",
    "catalog_magnitude",
)

REASON_QTY = "qty_unit_price_neq_total"
REASON_SHIFT = "decimal_shift"
REASON_COLLAPSE = "qty_eq_1_collapse"
REASON_ZERO = "zero_or_negative"
REASON_DUP = "duplicate_row"
REASON_CATALOG = "catalog_magnitude"

REF_KEYS = ("valor_referencia", "preco_referencia", "valor_referencia_catalogo")
SHIFT_BANDS = ((1.8, 2.2), (2.8, 3.2))
MIN_SHIFT_GROUP = 3
CATALOG_HIGH = Decimal("100")
CATALOG_LOW = Decimal("0.01")

SCHEMA = {
    "record_id": pl.String,
    "pncp_id": pl.String,
    "reason": pl.String,
    "detail": pl.String,
    "snapshot_id": pl.String,
    "methodology_version": pl.String,
}


def detect_data_errors(
    items: pl.DataFrame,
    *,
    catalog_prices: dict[str, Decimal] | None = None,
) -> pl.DataFrame:
    """Tag data-quality exclusions. A row may carry several reasons."""
    if items.is_empty():
        return pl.DataFrame(schema=SCHEMA)
    rows: list[dict] = []
    rows.extend(_from_qty_mismatch(items))
    rows.extend(_decimal_shift(items))
    rows.extend(_qty_eq_1_collapse(items))
    rows.extend(_zero_or_negative(items))
    rows.extend(_duplicate_row(items))
    rows.extend(_catalog_magnitude(items, catalog_prices))
    return pl.DataFrame(rows, schema=SCHEMA) if rows else pl.DataFrame(schema=SCHEMA)


def anomaly_pool(items: pl.DataFrame, exclusions: pl.DataFrame) -> pl.DataFrame:
    """Drop any item that has an exclusion reason. Explorer rows stay elsewhere."""
    if items.is_empty() or exclusions is None or exclusions.is_empty():
        return items
    if "record_id" not in exclusions.columns:
        return items
    banned = {str(v) for v in exclusions["record_id"].to_list() if v}
    if not banned:
        return items
    return items.filter(~pl.col("record_id").is_in(sorted(banned)))


def catalog_reference_prices(catalog_df: pl.DataFrame | None) -> dict[str, Decimal]:
    """Read planted catalog reference prices. Empty when the catalog has none."""
    if catalog_df is None or catalog_df.is_empty():
        return {}
    folded = {fold(c).replace(" ", "").replace("_", ""): c for c in catalog_df.columns}
    code_col = None
    for alias in ("codigo", "codigoitem", "codigoservico", "coditemcatalogo"):
        if alias in folded:
            code_col = folded[alias]
            break
    ref_col = None
    for alias in ("valorreferencia", "precoreferencia", "valorreferenciacatalogo"):
        if alias in folded:
            ref_col = folded[alias]
            break
    if not code_col or not ref_col:
        return {}
    out: dict[str, Decimal] = {}
    for row in catalog_df.iter_rows(named=True):
        code = str(row.get(code_col) or "").strip()
        price = parse_decimal(row.get(ref_col))
        if not code or price is None or price <= 0:
            continue
        out[code] = price
    return out


def fixture_items_path(root: Path | None = None) -> Path:
    base = root or _repo_root()
    path = base / "detect" / "fixtures" / "data_error" / "items.csv"
    if not path.exists():
        raise FileNotFoundError(f"data-error golden fixture missing: {path}")
    return path


def _from_qty_mismatch(items: pl.DataFrame) -> list[dict]:
    flags = detect_qty_price_mismatch(items)
    rows: list[dict] = []
    for row in flags.iter_rows(named=True):
        rows.append(
            _tag(
                {
                    "record_id": row.get("record_id"),
                    "pncp_id": row.get("pncp_id"),
                    "snapshot_id": row.get("snapshot_id"),
                    "methodology_version": row.get("methodology_version"),
                },
                REASON_QTY,
                str(row.get("delta") or "qty * unit_price != total_value"),
            )
        )
    return rows


def _decimal_shift(items: pl.DataFrame) -> list[dict]:
    groups: dict[tuple[str, str], list[tuple[dict, Decimal]]] = defaultdict(list)
    for row in items.iter_rows(named=True):
        key = _peer_key(row)
        price = parse_decimal(row.get("valor_unitario"))
        if key is None or price is None or price <= 0:
            continue
        groups[key].append((row, price))
    rows: list[dict] = []
    for key, recs in groups.items():
        if len(recs) < MIN_SHIFT_GROUP:
            continue
        median = _median([price for _, price in recs])
        if median is None or median <= 0:
            continue
        for row, price in recs:
            mag = _abs_log10(price, median)
            if mag is None or not _in_shift_band(mag):
                continue
            rows.append(
                _tag(
                    row,
                    REASON_SHIFT,
                    (
                        f"unit_price is a 100x or 1000x shift from peer median. "
                        f"peer={key[0]}:{key[1]} price={price} median={median} abs_log10={mag:.4f}"
                    ),
                )
            )
    return rows


def _qty_eq_1_collapse(items: pl.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for row in items.iter_rows(named=True):
        qty = parse_decimal(row.get("quantidade"))
        unit = parse_decimal(row.get("valor_unitario"))
        total = parse_decimal(row.get("valor_total"))
        if qty != Decimal("1") or unit is None or total is None:
            continue
        if unit != total:
            continue
        rows.append(
            _tag(
                row,
                REASON_COLLAPSE,
                f"quantidade==1 and unit_price==total_value. qty={qty} unit_price={unit} total={total}",
            )
        )
    return rows


def _zero_or_negative(items: pl.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for row in items.iter_rows(named=True):
        qty = parse_decimal(row.get("quantidade"))
        unit = parse_decimal(row.get("valor_unitario"))
        total = parse_decimal(row.get("valor_total"))
        hits: list[str] = []
        if qty is not None and qty <= 0:
            hits.append(f"quantidade={qty}")
        if unit is not None and unit <= 0:
            hits.append(f"valor_unitario={unit}")
        if total is not None and total < 0:
            hits.append(f"valor_total={total}")
        if not hits:
            continue
        rows.append(_tag(row, REASON_ZERO, "non-positive money or qty. " + " ".join(hits)))
    return rows


def _duplicate_row(items: pl.DataFrame) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in items.iter_rows(named=True):
        key = _dup_key(row)
        if key is None:
            continue
        groups[key].append(row)
    rows: list[dict] = []
    for key, recs in groups.items():
        if len(recs) < 2:
            continue
        ordered = sorted(recs, key=lambda r: str(r.get("record_id") or ""))
        canonical = str(ordered[0].get("record_id") or "")
        for extra in ordered[1:]:
            rows.append(
                _tag(
                    extra,
                    REASON_DUP,
                    (
                        f"duplicate pncp+item+money. canonical_record_id={canonical} "
                        f"pncp_id={key[0]} item={key[1]}"
                    ),
                )
            )
    return rows


def _catalog_magnitude(
    items: pl.DataFrame,
    catalog_prices: dict[str, Decimal] | None,
) -> list[dict]:
    prices = catalog_prices or {}
    rows: list[dict] = []
    for row in items.iter_rows(named=True):
        ref = _row_reference(row, prices)
        if ref is None or ref <= 0:
            continue
        unit = parse_decimal(row.get("valor_unitario"))
        if unit is None or unit <= 0:
            continue
        ratio = unit / ref
        if ratio <= CATALOG_HIGH and ratio >= CATALOG_LOW:
            continue
        rows.append(
            _tag(
                row,
                REASON_CATALOG,
                f"unit_price vs catalog reference is >100x or <0.01x. price={unit} ref={ref} ratio={ratio}",
            )
        )
    return rows


def _row_reference(row: dict, catalog_prices: dict[str, Decimal]) -> Decimal | None:
    for key in REF_KEYS:
        planted = parse_decimal(row.get(key))
        if planted is not None and planted > 0:
            return planted
    for code in (row.get("catmat"), row.get("catser")):
        token = str(code or "").strip()
        if token and token in catalog_prices:
            return catalog_prices[token]
    return None


def _peer_key(row: dict) -> tuple[str, str] | None:
    catmat = str(row.get("catmat") or "").strip()
    if catmat:
        return ("catmat", catmat)
    catser = str(row.get("catser") or "").strip()
    if catser:
        return ("catser", catser)
    desc = fold(str(row.get("descricao") or ""))
    if desc:
        return ("desc", desc)
    return None


def _dup_key(row: dict) -> tuple | None:
    pncp = str(row.get("pncp_id") or "").strip()
    item_no = str(
        row.get("id_compra_item")
        or row.get("numero_item")
        or row.get("numeroitemcompra")
        or ""
    ).strip()
    desc = fold(str(row.get("descricao") or ""))
    item_part = item_no or desc
    if not pncp or not item_part:
        return None
    return (
        pncp,
        item_part,
        _dec_key(parse_decimal(row.get("quantidade"))),
        _dec_key(parse_decimal(row.get("valor_unitario"))),
        _dec_key(parse_decimal(row.get("valor_total"))),
    )


def _tag(row: dict, reason: str, detail: str) -> dict:
    return {
        "record_id": str(row.get("record_id") or ""),
        "pncp_id": str(row.get("pncp_id") or ""),
        "reason": reason,
        "detail": detail,
        "snapshot_id": str(row.get("snapshot_id") or ""),
        "methodology_version": str(row.get("methodology_version") or ""),
    }


def _median(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    if n % 2:
        return ordered[n // 2]
    return (ordered[n // 2 - 1] + ordered[n // 2]) / 2


def _abs_log10(price: Decimal, median: Decimal) -> float | None:
    if price <= 0 or median <= 0:
        return None
    ratio = float(price / median)
    if ratio <= 0:
        return None
    return abs(log10(ratio))


def _in_shift_band(mag: float) -> bool:
    return any(lo <= mag <= hi for lo, hi in SHIFT_BANDS)


def _dec_key(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value, "f")


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "detect" / "fixtures" / "data_error" / "items.csv").exists():
            return p
        if (p / "infra" / "postgres" / "01_compras.sql").exists():
            return p
    raise RuntimeError("repo root not found")
