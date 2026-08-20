from __future__ import annotations

from datetime import date

import polars as pl

from compras_detect.tier1.common import award_date, flag, to_frame
from compras_normalize.text import fold, parse_date


def detect_sanctioned(items: pl.DataFrame, sanctions: pl.DataFrame | None) -> pl.DataFrame:
    if sanctions is None or sanctions.is_empty() or items.is_empty():
        return to_frame([])
    by_cnpj = _sanctions_by_cnpj(sanctions)
    if not by_cnpj:
        return to_frame([])
    rows: list[dict] = []
    seen: set[str] = set()
    for row in items.iter_rows(named=True):
        cnpj = "".join(c for c in str(row.get("fornecedor_cnpj") or "") if c.isdigit())
        if len(cnpj) != 14 or cnpj not in by_cnpj:
            continue
        award = award_date(row)
        if award is None:
            continue
        hit = _first_overlap(by_cnpj[cnpj], award)
        if hit is None:
            continue
        key = f"{row.get('record_id')}:{cnpj}"
        if key in seen:
            continue
        seen.add(key)
        cadastro, ref = hit
        rows.append(
            flag(
                row,
                "sanctioned_ceis_cnep",
                (
                    f"fornecedor CNPJ overlaps {cadastro} sanction window "
                    f"on award_date={award.isoformat()}. ref={ref}"
                ),
            )
        )
    return to_frame(rows)


def _first_overlap(rows: list[tuple[date | None, date | None, str, str]], award: date) -> tuple[str, str] | None:
    for start, end, cadastro, ref in rows:
        if _overlaps(award, start, end):
            return cadastro, ref
    return None


def _overlaps(award: date, start: date | None, end: date | None) -> bool:
    if start is not None and award < start:
        return False
    if end is not None and award > end:
        return False
    return True


def _sanctions_by_cnpj(sanctions: pl.DataFrame) -> dict[str, list[tuple[date | None, date | None, str, str]]]:
    out: dict[str, list[tuple[date | None, date | None, str, str]]] = {}
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
        start = parse_date(
            folded.get("datainiciosancao")
            or folded.get("datainicio")
        )
        end = parse_date(
            folded.get("datafinalsancao")
            or folded.get("datafimsancao")
            or folded.get("datafim")
            or folded.get("datafimdoefeito")
            or folded.get("fimvigencia")
        )
        cadastro = str(folded.get("cadastro") or folded.get("fonte") or "CEIS/CNEP")
        ref = str(folded.get("codigodasancao") or folded.get("id") or digits)
        out.setdefault(digits, []).append((start, end, cadastro, ref))
    return out
