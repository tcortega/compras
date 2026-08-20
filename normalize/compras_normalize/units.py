from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import polars as pl

from compras_normalize.text import fold, parse_decimal

_DATA = Path(__file__).resolve().parent / "data" / "unidade_medida.csv"
_TRAIL = re.compile(r"[.:;]+$")
_PACK = re.compile(
    r"^(?P<pack>cx|cxa|caixa|cxs|pct|pcte|pacote|resma|fardo|cento|centena|duzia|dz)"
    r"(?:\s*(?:c/|x|/)\s*|\s+)(?P<n>\d+(?:[.,]\d+)?)$"
)
_QTY_UNIT = re.compile(
    r"^(?:(?P<head>[a-z][a-z0-9]*)\s+)?"
    r"(?P<n>\d+(?:[.,]\d+)?)\s*"
    r"(?P<u>ml|mililitros?|mg|miligramas?|g|gr|grs|gramas?|kg|quilogramas?|"
    r"l|lt|lts|litros?|m3|m³|m2|m²|cm|mm|m|mts?|metros?)$"
)
_PACK_TO_UN = frozenset(
    {"cx", "cxa", "caixa", "cxs", "pct", "pcte", "pacote", "cento", "centena", "duzia", "dz"}
)
_MEASURE = {
    "ml": ("l", Decimal("0.001")),
    "mililitro": ("l", Decimal("0.001")),
    "mililitros": ("l", Decimal("0.001")),
    "l": ("l", Decimal("1")),
    "lt": ("l", Decimal("1")),
    "lts": ("l", Decimal("1")),
    "litro": ("l", Decimal("1")),
    "litros": ("l", Decimal("1")),
    "mg": ("kg", Decimal("0.000001")),
    "miligrama": ("kg", Decimal("0.000001")),
    "miligramas": ("kg", Decimal("0.000001")),
    "g": ("kg", Decimal("0.001")),
    "gr": ("kg", Decimal("0.001")),
    "grs": ("kg", Decimal("0.001")),
    "grama": ("kg", Decimal("0.001")),
    "gramas": ("kg", Decimal("0.001")),
    "kg": ("kg", Decimal("1")),
    "quilograma": ("kg", Decimal("1")),
    "quilogramas": ("kg", Decimal("1")),
    "m3": ("m3", Decimal("1")),
    "m³": ("m3", Decimal("1")),
    "m2": ("m2", Decimal("1")),
    "m²": ("m2", Decimal("1")),
    "cm": ("m", Decimal("0.01")),
    "mm": ("m", Decimal("0.001")),
    "m": ("m", Decimal("1")),
    "mt": ("m", Decimal("1")),
    "mts": ("m", Decimal("1")),
    "metro": ("m", Decimal("1")),
    "metros": ("m", Decimal("1")),
}


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
        key = _key(raw)
        if key == "":
            return UnitMatch("", "unknown", Decimal("1"), "unknown", "unknown")
        hit = self.by_raw.get(key) or self.by_raw.get(key.replace(" ", ""))
        if hit:
            return hit
        compact = key.replace(" ", "")
        best: UnitMatch | None = None
        best_n = 0
        for stored, match in self.by_raw.items():
            n = len(stored)
            if n < 2 or n <= best_n:
                continue
            if key.startswith(stored + " ") or key.startswith(stored + "/") or key.startswith(stored + "x"):
                best, best_n = match, n
                continue
            if compact.startswith(stored) and len(compact) > n and compact[n].isdigit():
                best, best_n = match, n
        if best:
            return best
        parsed = _parse_structured(raw or "", key)
        if parsed:
            return parsed
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
        folded = _key(match.raw)
        by_raw[folded] = match
        by_raw[folded.replace(" ", "")] = match
    return UnitTable(by_raw)


def _key(raw: str | None) -> str:
    return _TRAIL.sub("", fold(raw))


def _parse_structured(raw: str, key: str) -> UnitMatch | None:
    pack = _PACK.match(key)
    if pack:
        n = parse_decimal(pack.group("n"))
        token = pack.group("pack")
        if n is None or n == 0:
            return None
        if token == "resma":
            return UnitMatch(raw, "folha", n, "folha", "parsed")
        if token in _PACK_TO_UN:
            return UnitMatch(raw, "un", n, "un", "parsed")
    qty = _QTY_UNIT.match(key)
    if qty:
        n = parse_decimal(qty.group("n"))
        unit = qty.group("u")
        if n is None or n == 0:
            return None
        base = _MEASURE.get(unit)
        if not base:
            return None
        canonical, unit_factor = base
        return UnitMatch(raw, canonical, n * unit_factor, canonical, "parsed")
    return None
