from __future__ import annotations

from datetime import timedelta

import polars as pl

from compras_detect.tier1.common import flag, to_frame
from compras_normalize.text import parse_date, parse_datetime

MAX_DAYS = 90


def detect_cnpj_age(items: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    for row in items.iter_rows(named=True):
        opened = parse_date(row.get("opened_on"))
        publicado = parse_datetime(row.get("publicado_em"))
        if opened is None or publicado is None:
            continue
        age = publicado.date() - opened
        if age.days < 0 or age > timedelta(days=MAX_DAYS):
            continue
        rows.append(
            flag(
                row,
                "cnpj_age",
                f"fornecedor openedOn is {age.days} days before publicadoEm. openedOn={opened.isoformat()} publicadoEm={publicado.date().isoformat()}",
            )
        )
    return to_frame(rows)
