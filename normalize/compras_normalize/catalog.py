from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl

from compras_normalize.text import fold

_CODE_ALIASES = ("codigo", "codigoitem", "coditemcatalogo", "codigoitemcatalogo", "coditem")
_DESC_ALIASES = ("descricao", "descricaoitem", "descricaoitemcatalogo", "nome")
_TIPO_ALIASES = ("tipo", "materialouservico", "natureza")


@dataclass(frozen=True)
class CatalogHit:
    catmat: str | None
    catser: str | None
    quality: str


@dataclass
class Catalog:
    by_code_m: dict[str, str]
    by_code_s: dict[str, str]
    by_desc_m: dict[str, str]
    by_desc_s: dict[str, str]
    tokens_m: list[tuple[str, set[str], str]]
    tokens_s: list[tuple[str, set[str], str]]

    def match(
        self,
        descricao: str | None,
        codigo: str | None,
        material_ou_servico: str | None,
    ) -> CatalogHit:
        code = (codigo or "").strip()
        kind = (material_ou_servico or "").strip().upper()[:1]
        if code:
            if kind == "S" or code in self.by_code_s:
                if code in self.by_code_s or kind == "S":
                    return CatalogHit(None, code, "exact")
            return CatalogHit(code, None, "exact")
        key = fold(descricao)
        if key == "":
            return CatalogHit(None, None, "none")
        if kind != "S" and key in self.by_desc_m:
            return CatalogHit(self.by_desc_m[key], None, "exact")
        if kind != "M" and key in self.by_desc_s:
            return CatalogHit(None, self.by_desc_s[key], "exact")
        tokens = _tokens(key)
        if not tokens:
            return CatalogHit(None, None, "none")
        best: tuple[float, str, str] | None = None
        pool = self.tokens_s if kind == "S" else self.tokens_m
        if kind == "":
            pool = self.tokens_m + self.tokens_s
        for code_i, tok, tipo in pool:
            overlap = len(tokens & tok)
            denom = max(len(tokens), len(tok))
            if denom == 0:
                continue
            score = overlap / denom
            if best is None or score > best[0]:
                best = (score, code_i, tipo)
        if best and best[0] >= 0.8:
            if best[2] == "S":
                return CatalogHit(None, best[1], "fuzzy")
            return CatalogHit(best[1], None, "fuzzy")
        return CatalogHit(None, None, "none")


def load_catalog(frames: list[pl.DataFrame]) -> Catalog:
    by_code_m: dict[str, str] = {}
    by_code_s: dict[str, str] = {}
    by_desc_m: dict[str, str] = {}
    by_desc_s: dict[str, str] = {}
    tokens_m: list[tuple[str, set[str], str]] = []
    tokens_s: list[tuple[str, set[str], str]] = []
    for df in frames:
        if df.is_empty():
            continue
        mapped = _map_cols(df)
        for row in mapped.iter_rows(named=True):
            code = str(row["codigo"]).strip()
            desc = str(row["descricao"])
            tipo = str(row["tipo"]).strip().upper()[:1] or "M"
            if not code:
                continue
            key = fold(desc)
            if tipo == "S":
                by_code_s[code] = desc
                if key:
                    by_desc_s[key] = code
                    tokens_s.append((code, _tokens(key), "S"))
            else:
                by_code_m[code] = desc
                if key:
                    by_desc_m[key] = code
                    tokens_m.append((code, _tokens(key), "M"))
    return Catalog(by_code_m, by_code_s, by_desc_m, by_desc_s, tokens_m, tokens_s)


def load_catalog_from_dir(path: Path) -> Catalog:
    frames: list[pl.DataFrame] = []
    for p in sorted(path.rglob("*.csv")):
        frames.append(pl.read_csv(p, separator=";", infer_schema_length=0, encoding="utf8-lossy"))
    return load_catalog(frames)


def _map_cols(df: pl.DataFrame) -> pl.DataFrame:
    rename: dict[str, str] = {}
    for c in df.columns:
        k = fold(c).replace(" ", "")
        if k in _CODE_ALIASES:
            rename[c] = "codigo"
        elif k in _DESC_ALIASES:
            rename[c] = "descricao"
        elif k in _TIPO_ALIASES:
            rename[c] = "tipo"
    out = df.rename(rename)
    if "codigo" not in out.columns or "descricao" not in out.columns:
        raise ValueError(f"catalog missing codigo/descricao: {df.columns}")
    if "tipo" not in out.columns:
        out = out.with_columns(pl.lit("M").alias("tipo"))
    return out.select("codigo", "descricao", "tipo")


def _tokens(key: str) -> set[str]:
    return {t for t in key.split() if len(t) > 2}
