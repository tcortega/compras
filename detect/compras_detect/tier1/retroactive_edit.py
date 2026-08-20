from __future__ import annotations

from collections import defaultdict

import polars as pl

from compras_detect.tier1.common import flag, to_frame


def detect_retroactive_edits(landing_records: pl.DataFrame | None) -> pl.DataFrame:
    if landing_records is None or landing_records.is_empty():
        return to_frame([])
    by_id: dict[str, list[dict]] = defaultdict(list)
    for row in landing_records.iter_rows(named=True):
        rid = str(row.get("record_id") or "")
        if rid:
            by_id[rid].append(row)
    rows: list[dict] = []
    for rid, recs in by_id.items():
        hashes = []
        for rec in recs:
            h = str(rec.get("record_hash") or "")
            if h and h not in hashes:
                hashes.append(h)
        if len(hashes) < 2:
            continue
        latest = recs[-1]
        rows.append(
            flag(
                latest,
                "retroactive_edit",
                f"record content hash changed after publication. record_id={rid} hashes={' -> '.join(hashes)}",
            )
        )
    return to_frame(rows)
