from __future__ import annotations

import polars as pl

from compras_detect.tier1.common import award_date, flag, to_frame
from compras_normalize.text import parse_date

FLAG_DAYS = 90
INFO_DAYS = 365
KIND_AGE = "cnpj_age"
KIND_AGE_INFO = "cnpj_age_info"


def detect_cnpj_age(items: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    for row in items.iter_rows(named=True):
        opened = parse_date(row.get("opened_on"))
        award = award_date(row)
        if opened is None or award is None:
            continue
        age_days = (award - opened).days
        if age_days < 0:
            continue
        if age_days < FLAG_DAYS:
            kind = KIND_AGE
            tier = "flag"
        elif age_days < INFO_DAYS:
            kind = KIND_AGE_INFO
            tier = "info"
        else:
            continue
        rows.append(
            flag(
                row,
                kind,
                (
                    f"opened_on={opened.isoformat()} award_date={award.isoformat()} "
                    f"age_days={age_days} tier={tier}"
                ),
            )
        )
    return to_frame(rows)
