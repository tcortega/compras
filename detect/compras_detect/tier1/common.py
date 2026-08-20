from __future__ import annotations

from datetime import date

import polars as pl

from compras_normalize.text import parse_date

SCHEMA = {
    "record_id": pl.String,
    "pncp_id": pl.String,
    "kind": pl.String,
    "delta": pl.String,
    "source_url": pl.String,
    "snapshot_id": pl.String,
    "methodology_version": pl.String,
}


def flag(row: dict, kind: str, delta: str) -> dict:
    return {
        "record_id": str(row.get("record_id") or ""),
        "pncp_id": str(row.get("pncp_id") or ""),
        "kind": kind,
        "delta": delta,
        "source_url": str(row.get("source_url") or ""),
        "snapshot_id": str(row.get("snapshot_id") or ""),
        "methodology_version": str(row.get("methodology_version") or ""),
    }


def empty() -> pl.DataFrame:
    return pl.DataFrame(schema=SCHEMA)


def to_frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows) if rows else empty()


def award_date(row: dict) -> date | None:
    return parse_date(row.get("award_date") or row.get("data_resultado") or row.get("publicado_em"))
