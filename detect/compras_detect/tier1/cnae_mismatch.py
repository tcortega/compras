from __future__ import annotations

import polars as pl

from compras_detect.tier1.common import flag, to_frame

# Finance and domestic CNAE sections vs material purchase.
_FINANCE = {"64", "65", "66"}
_DOMESTIC = {"97", "98"}


def detect_cnae_mismatch(items: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    for row in items.iter_rows(named=True):
        cnae = "".join(c for c in str(row.get("cnae") or "") if c.isdigit())
        if len(cnae) < 2:
            continue
        section = cnae[:2]
        tipo = str(row.get("material_ou_servico") or "").upper()[:1]
        catalog = str(row.get("catmat") or row.get("catser") or "")
        if tipo == "S":
            continue
        if section in _FINANCE or section in _DOMESTIC:
            rows.append(
                flag(
                    row,
                    "cnae_mismatch",
                    f"CNAE {cnae} section {section} is outside expected classes for a material purchase. catalog={catalog}",
                )
            )
    return to_frame(rows)
