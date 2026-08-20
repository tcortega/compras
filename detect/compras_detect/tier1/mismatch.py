from __future__ import annotations

from decimal import Decimal

import polars as pl

from compras_detect.tier1.common import flag, to_frame
from compras_normalize.text import parse_decimal


def detect_qty_price_mismatch(items: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    for row in items.iter_rows(named=True):
        qty = parse_decimal(row.get("quantidade"))
        unit = parse_decimal(row.get("valor_unitario"))
        total = parse_decimal(row.get("valor_total"))
        if qty is None or unit is None or total is None:
            continue
        expected = qty * unit
        abs_err = abs(expected - total)
        scale = max(abs(total), abs(expected), Decimal("1"))
        if abs_err <= Decimal("0.02") or (abs_err / scale) <= Decimal("0.002"):
            continue
        rows.append(
            flag(
                row,
                "qty_unit_price_neq_total",
                f"qty * unit_price != total_value. qty={qty} unit_price={unit} product={expected} total={total}",
            )
        )
    return to_frame(rows)
