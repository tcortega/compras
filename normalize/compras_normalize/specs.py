from __future__ import annotations

import re
from dataclasses import dataclass

from compras_normalize.text import fold

# Raw tokens only. Do not invent a unit. Absent stays null.
_CONC = re.compile(
    r"(?<![a-z0-9])(\d+(?:[.,]\d+)?\s*mg\s*/\s*ml)(?![a-z0-9])",
    re.I,
)
_DOSAGE_MG = re.compile(
    r"(?<![a-z0-9])(\d+(?:[.,]\d+)?\s*mg)(?!\s*/)",
    re.I,
)
_DOSAGE_COMPR = re.compile(
    r"(?<![a-z0-9])(\d+(?:[.,]\d+)?\s*compr\.?(?:imidos?)?)(?![a-z0-9])",
    re.I,
)
_SIZE_ML = re.compile(
    r"(?<![a-z0-9])(\d+(?:[.,]\d+)?\s*ml)(?![a-z0-9])",
    re.I,
)
_SIZE_G = re.compile(
    r"(?<![a-z0-9])(\d+(?:[.,]\d+)?\s*g)(?![a-z0-9])",
    re.I,
)
_SIZE_FOLHA = re.compile(
    r"(?<![a-z0-9])(\d+(?:[.,]\d+)?\s*folhas?)(?![a-z0-9])",
    re.I,
)
_SIZE_PAPER = re.compile(r"(?<![a-z0-9])(a[3-6])(?![a-z0-9])", re.I)


@dataclass(frozen=True)
class SpecFields:
    concentracao: str | None
    dosagem: str | None
    tamanho: str | None


def extract_specs(descricao: str | None) -> SpecFields:
    raw = descricao or ""
    if raw.strip() == "":
        return SpecFields(None, None, None)
    key = fold(raw)
    conc = _first(_CONC, key)
    dose = None
    if conc is None:
        dose = _first(_DOSAGE_MG, key) or _first(_DOSAGE_COMPR, key)
    else:
        dose = _first(_DOSAGE_COMPR, key)
    size = _first(_SIZE_ML, key)
    if size and conc and _same_token(size, conc):
        size = None
    if size is None:
        size = _first(_SIZE_FOLHA, key) or _first(_SIZE_PAPER, key) or _first(_SIZE_G, key)
    if size and conc and _token_inside(size, conc):
        size = _first(_SIZE_FOLHA, key) or _first(_SIZE_PAPER, key)
    return SpecFields(_raw_token(conc), _raw_token(dose), _raw_token(size))


def _first(pat: re.Pattern[str], text: str) -> str | None:
    m = pat.search(text)
    return m.group(1) if m else None


def _raw_token(value: str | None) -> str | None:
    if value is None:
        return None
    token = re.sub(r"\s+", "", value.strip().lower())
    return token or None


def _same_token(a: str, b: str) -> bool:
    return _raw_token(a) == _raw_token(b)


def _token_inside(part: str, whole: str) -> bool:
    p = _raw_token(part) or ""
    w = _raw_token(whole) or ""
    return bool(p) and p in w
