from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

import polars as pl

from compras_detect.tier1.common import flag, to_frame
from compras_normalize.text import fold, parse_decimal

# Decreto 11.871/2023 (2024) and Decreto 12.343/2024 (2025). Art. 75 I/II.
_THRESH = {
    2024: {"obras": Decimal("119812.02"), "compras": Decimal("59906.02")},
    2025: {"obras": Decimal("125451.15"), "compras": Decimal("62725.59")},
}


def detect_fracionamento(items: pl.DataFrame) -> pl.DataFrame:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in items.iter_rows(named=True):
        if not _is_dispensa(row):
            continue
        catalog = str(row.get("catmat") or row.get("catser") or "")
        if catalog == "":
            continue
        ano = str(row.get("ano") or "")[:4]
        orgao = str(row.get("orgao_cnpj") or "")
        if not ano or not orgao:
            continue
        groups[(orgao, catalog, ano)].append(row)
    rows: list[dict] = []
    for (orgao, catalog, ano), recs in groups.items():
        if len(recs) < 2:
            continue
        year = int(ano)
        kind = "obras" if _looks_obra(recs) else "compras"
        table = _THRESH.get(year) or _THRESH[2024]
        threshold = table[kind]
        values: list[Decimal] = []
        for rec in recs:
            v = parse_decimal(rec.get("valor_total")) or parse_decimal(rec.get("valor_homologado"))
            if v is None:
                continue
            values.append(v)
        if len(values) < 2:
            continue
        if any(v >= threshold for v in values):
            continue
        total = sum(values, Decimal("0"))
        if total <= threshold:
            continue
        sample = recs[0]
        rows.append(
            flag(
                sample,
                "fracionamento",
                (
                    f"same orgao+catalog spend in fiscal year exceeds Art. 75 {kind} threshold "
                    f"while each contratacao is under it. orgao={orgao} catalog={catalog} "
                    f"year={ano} n={len(values)} sum={total} threshold={threshold}"
                ),
            )
        )
    return to_frame(rows)


def _is_dispensa(row: dict) -> bool:
    nome = fold(str(row.get("modalidade") or ""))
    codigo = str(row.get("modalidade_codigo") or "").strip()
    return codigo == "8" or "dispensa" in nome


def _looks_obra(recs: list[dict]) -> bool:
    blob = " ".join(fold(str(r.get("objeto") or "")) + " " + fold(str(r.get("descricao") or "")) for r in recs)
    return "obra" in blob or "engenharia" in blob
