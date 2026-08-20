from __future__ import annotations

from datetime import date

import polars as pl

from compras_detect.tier1.common import flag, to_frame
from compras_normalize.text import fold, parse_date


def detect_sanctioned(items: pl.DataFrame, sanctions: pl.DataFrame | None) -> pl.DataFrame:
    if sanctions is None or sanctions.is_empty() or items.is_empty():
        return to_frame([])
    active = _active_cnpjs(sanctions)
    if not active:
        return to_frame([])
    rows: list[dict] = []
    seen: set[str] = set()
    for row in items.iter_rows(named=True):
        cnpj = "".join(c for c in str(row.get("fornecedor_cnpj") or "") if c.isdigit())
        if len(cnpj) != 14 or cnpj not in active:
            continue
        key = f"{row.get('record_id')}:{cnpj}"
        if key in seen:
            continue
        seen.add(key)
        cadastro, ref = active[cnpj]
        rows.append(
            flag(
                row,
                "sanctioned_ceis_cnep",
                f"fornecedor CNPJ present in {cadastro} snapshot. ref={ref}",
            )
        )
    return to_frame(rows)


def _active_cnpjs(sanctions: pl.DataFrame) -> dict[str, tuple[str, str]]:
    today = date.today()
    out: dict[str, tuple[str, str]] = {}
    for row in sanctions.iter_rows(named=True):
        folded = {fold(k).replace(" ", "").replace("_", ""): v for k, v in row.items()}
        raw = str(
            folded.get("cpfoucnpjdosancionado")
            or folded.get("cpfcnpj")
            or folded.get("cnpj")
            or folded.get("cpfoucnpj")
            or ""
        )
        digits = "".join(c for c in raw if c.isdigit())
        if len(digits) != 14:
            continue
        end = parse_date(
            folded.get("datafimdoefeito")
            or folded.get("datafim")
            or folded.get("fimvigencia")
        )
        if end is not None and end < today:
            continue
        cadastro = str(folded.get("cadastro") or folded.get("fonte") or "CEIS/CNEP")
        ref = str(folded.get("codigodasancao") or folded.get("id") or digits)
        out[digits] = (cadastro, ref)
    return out
