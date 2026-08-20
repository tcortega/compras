from __future__ import annotations

from pathlib import Path

import polars as pl


def read_csv(path: Path, separator: str | None = None, has_header: bool = True) -> pl.DataFrame:
    sep = separator or _sniff_separator(path)
    return pl.read_csv(
        path,
        separator=sep,
        infer_schema_length=0,
        encoding="utf8-lossy",
        has_header=has_header,
        truncate_ragged_lines=True,
        try_parse_dates=False,
    )


def _sniff_separator(path: Path) -> str:
    sample = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not sample:
        return ";"
    header = sample[0]
    if header.count(";") >= header.count(",") and header.count(";") >= header.count("\t"):
        return ";"
    if header.count("\t") > header.count(","):
        return "\t"
    return ","
