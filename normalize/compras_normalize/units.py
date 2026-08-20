from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import polars as pl

from compras_normalize.text import fold, parse_decimal

_DATA = Path(__file__).resolve().parent / "data" / "unidade_medida.csv"


@dataclass(frozen=True)
class UnitMatch:
    raw: str
    canonical: str
    to_base_factor: Decimal
    base_unit: str
    confidence: str


@dataclass
class UnitTable:
    by_raw: dict[str, UnitMatch]

    def match(self, raw: str | None) -> UnitMatch:
        key = fold(raw)
        if key == "":
            return UnitMatch("", "unknown", Decimal("1"), "unknown", "unknown")
        hit = self.by_raw.get(key)
        if hit:
            return hit
        compact = key.replace(" ", "")
        hit = self.by_raw.get(compact)
        if hit:
            return hit
        for stored, match in self.by_raw.items():
            if stored and (key.startswith(stored + " ") or compact.startswith(stored)):
                return match
        return UnitMatch(raw or "", "unknown", Decimal("1"), "unknown", "unknown")


def load_unit_table(path: Path | None = None) -> UnitTable:
    src = path or _DATA
    df = pl.read_csv(src, separator=";", infer_schema_length=0)
    by_raw: dict[str, UnitMatch] = {}
    for row in df.iter_rows(named=True):
        match = UnitMatch(
            raw=str(row["raw"]),
            canonical=str(row["canonical"]),
            to_base_factor=parse_decimal(row["to_base_factor"]) or Decimal("1"),
            base_unit=str(row["base_unit"]),
            confidence="parsed",
        )
        by_raw[fold(match.raw)] = match
        by_raw[fold(match.raw).replace(" ", "")] = match
    return UnitTable(by_raw)
