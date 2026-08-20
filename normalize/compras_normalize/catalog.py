from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from compras_normalize.classifier import (
    QUALITY_EXACT,
    QUALITY_KNN,
    QUALITY_NONE,
    CatalogKnn,
    ClassifierCache,
    KnnScore,
    assign_knn,
    description_hash,
    llm_hook_blocked,
    llm_hook_enabled,
    optional_llm_classify,
)
from compras_normalize.text import fold

_CODE_ALIASES = ("codigo", "codigoitem", "coditemcatalogo", "codigoitemcatalogo", "coditem")
_DESC_ALIASES = ("descricao", "descricaoitem", "descricaoitemcatalogo", "nome")
_TIPO_ALIASES = ("tipo", "materialouservico", "natureza")


@dataclass(frozen=True)
class CatalogHit:
    catmat: str | None
    catser: str | None
    quality: str
    top1: float | None = None
    top2: float | None = None
    assigned: bool = False


@dataclass
class Catalog:
    by_code_m: dict[str, str]
    by_code_s: dict[str, str]
    by_desc_m: dict[str, str]
    by_desc_s: dict[str, str]
    tokens_m: list[tuple[str, set[str], str]]
    tokens_s: list[tuple[str, set[str], str]]
    knn: CatalogKnn | None = None
    cache: ClassifierCache = field(default_factory=lambda: ClassifierCache({}))

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
                    return CatalogHit(None, code, QUALITY_EXACT, assigned=True)
            return CatalogHit(code, None, QUALITY_EXACT, assigned=True)
        key = fold(descricao)
        if key == "":
            return CatalogHit(None, None, QUALITY_NONE)
        if kind != "S" and key in self.by_desc_m:
            return CatalogHit(self.by_desc_m[key], None, QUALITY_EXACT, assigned=True)
        if kind != "M" and key in self.by_desc_s:
            return CatalogHit(None, self.by_desc_s[key], QUALITY_EXACT, assigned=True)
        return self._classify_uncoded(key, kind)

    def _classify_uncoded(self, key: str, kind: str) -> CatalogHit:
        digest = description_hash(key)
        cached = self.cache.get(digest)
        if cached is not None:
            return _hit_from_score(cached)
        if self.knn is None:
            score = KnnScore(None, None, QUALITY_NONE, 0.0, 0.0, False)
            self.cache.put(digest, score)
            return _hit_from_score(score)
        self.cache.embeds += 1
        row, top1, top2 = self.knn.query(key, kind)
        assigned = bool(row) and assign_knn(top1, top2)
        if assigned and row is not None:
            if row.tipo == "S":
                score = KnnScore(None, row.code, QUALITY_KNN, top1, top2, True)
            else:
                score = KnnScore(row.code, None, QUALITY_KNN, top1, top2, True)
        else:
            score = KnnScore(None, None, QUALITY_NONE, top1, top2, False)
            if llm_hook_enabled() and not llm_hook_blocked():
                llm = optional_llm_classify(key)
                if llm is not None and llm.assigned:
                    score = llm
        self.cache.put(digest, score)
        return _hit_from_score(score)


def load_catalog(frames: list[pl.DataFrame]) -> Catalog:
    by_code_m: dict[str, str] = {}
    by_code_s: dict[str, str] = {}
    by_desc_m: dict[str, str] = {}
    by_desc_s: dict[str, str] = {}
    tokens_m: list[tuple[str, set[str], str]] = []
    tokens_s: list[tuple[str, set[str], str]] = []
    knn_rows: list[tuple[str, str, str]] = []
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
            knn_rows.append((code, key, tipo))
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
    knn = CatalogKnn(knn_rows) if knn_rows else None
    return Catalog(by_code_m, by_code_s, by_desc_m, by_desc_s, tokens_m, tokens_s, knn)


def load_catalog_from_dir(path: Path) -> Catalog:
    frames: list[pl.DataFrame] = []
    for p in sorted(path.rglob("*.csv")):
        frames.append(pl.read_csv(p, separator=";", infer_schema_length=0, encoding="utf8-lossy"))
    return load_catalog(frames)


def _hit_from_score(score: KnnScore) -> CatalogHit:
    return CatalogHit(score.catmat, score.catser, score.quality, score.top1, score.top2, score.assigned)


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
