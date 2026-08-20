from __future__ import annotations

import re

import polars as pl

# CONTRACT: ***.XXX.XXX-** keeps digits 4-9.
_CPF_DIGITS = re.compile(r"(?<!\d)(\d{3})(\d{3})(\d{3})(\d{2})(?!\d)")
_CPF_FMT = re.compile(r"(?<!\d)(\d{3})\.(\d{3})\.(\d{3})-(\d{2})(?!\d)")


def mask_cpf(value: str | None) -> str:
    if value is None:
        return ""
    s = str(value)
    if s == "":
        return s

    def _fmt(_m: re.Match[str]) -> str:
        return f"***.{_m.group(2)}.{_m.group(3)}-**"

    s = _CPF_FMT.sub(_fmt, s)
    s = _CPF_DIGITS.sub(_fmt, s)
    return s


def is_cpf(value: str | None) -> bool:
    if value is None:
        return False
    digits = "".join(c for c in str(value) if c.isdigit())
    return len(digits) == 11


def is_cnpj(value: str | None) -> bool:
    if value is None:
        return False
    digits = "".join(c for c in str(value) if c.isdigit())
    return len(digits) == 14


def mask_frame(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df
    exprs = []
    for col in df.columns:
        dtype = df.schema[col]
        if dtype != pl.String:
            continue
        exprs.append(pl.col(col).map_elements(mask_cpf, return_dtype=pl.String))
    if not exprs:
        return df
    return df.with_columns(exprs)


_UNMASKED_FMT = re.compile(r"(?<!\*)\d{3}\.\d{3}\.\d{3}-\d{2}")
_FIXTURE_RAW = re.compile(r"(?<!\d)12345678901(?!\d)")


def assert_no_raw_cpf(values: list[str]) -> None:
    for value in values:
        if value is None:
            continue
        s = str(value)
        if _UNMASKED_FMT.search(s):
            raise ValueError(f"raw CPF leaked: {s}")
        if _FIXTURE_RAW.search(s):
            raise ValueError(f"raw CPF leaked: {s}")
