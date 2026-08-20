from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from compras_normalize.text import fold

# Conservative. Quality over coverage. Named constants for the uncoded kNN gate.
KNN_COSINE_MIN = 0.72
KNN_MARGIN_MIN = 0.18
QUALITY_EXACT = "exact"
QUALITY_KNN = "knn"
QUALITY_NONE = "none"
QUALITY_FUZZY = "fuzzy"

_HASH_DIM = 4096
_NGRAMS = (3, 4)
_LLM_FLAG = "CLASSIFIER_LLM"


@dataclass(frozen=True)
class KnnScore:
    catmat: str | None
    catser: str | None
    quality: str
    top1: float
    top2: float
    assigned: bool


@dataclass
class ClassifierCache:
    """In-memory lookup by sha256(folded description). Second pass is a lookup."""

    rows: dict[str, KnnScore]
    embeds: int = 0
    hits: int = 0

    def get(self, desc_hash: str) -> KnnScore | None:
        hit = self.rows.get(desc_hash)
        if hit is not None:
            self.hits += 1
        return hit

    def put(self, desc_hash: str, score: KnnScore) -> None:
        self.rows[desc_hash] = score

    def write_parquet(self, path: Path) -> None:
        if not self.rows:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            return
        pl.DataFrame(
            [
                {
                    "hash": h,
                    "catmat": s.catmat or "",
                    "catser": s.catser or "",
                    "quality": s.quality,
                    "top1": s.top1,
                    "top2": s.top2,
                    "assigned": s.assigned,
                }
                for h, s in self.rows.items()
            ]
        ).write_parquet(path)

    def load_parquet(self, path: Path) -> None:
        if not path.exists():
            return
        df = pl.read_parquet(path)
        for row in df.iter_rows(named=True):
            self.rows[str(row["hash"])] = KnnScore(
                str(row["catmat"]) or None,
                str(row["catser"]) or None,
                str(row["quality"]),
                float(row["top1"]),
                float(row["top2"]),
                bool(row["assigned"]),
            )


class HashEmbedder:
    """Signed char n-gram hashing vector. Deterministic. No network. No paid API."""

    def __init__(self, dim: int = _HASH_DIM, ngrams: tuple[int, ...] = _NGRAMS) -> None:
        self.dim = dim
        self.ngrams = ngrams
        self._idf: dict[int, float] = {}
        self._ready = False

    def fit(self, documents: list[str]) -> None:
        df: dict[int, int] = {}
        n = 0
        for doc in documents:
            seen: set[int] = set()
            for bucket, _sign, _tf in self._sparse_tf(doc):
                seen.add(bucket)
            if not seen:
                continue
            n += 1
            for bucket in seen:
                df[bucket] = df.get(bucket, 0) + 1
        idf: dict[int, float] = {}
        for bucket, count in df.items():
            idf[bucket] = math.log((n + 1) / (count + 1)) + 1.0
        self._idf = idf
        self._ready = True

    def embed(self, text: str) -> dict[int, float]:
        if not self._ready:
            raise RuntimeError("HashEmbedder.fit must run before embed")
        raw: dict[int, float] = {}
        for bucket, sign, tf in self._sparse_tf(text):
            weight = sign * tf * self._idf.get(bucket, 1.0)
            raw[bucket] = raw.get(bucket, 0.0) + weight
        return _l2_normalize(raw)

    def _sparse_tf(self, text: str) -> list[tuple[int, int, float]]:
        grams = _char_ngrams(text, self.ngrams)
        if not grams:
            return []
        counts: dict[str, int] = {}
        for gram in grams:
            counts[gram] = counts.get(gram, 0) + 1
        n = len(grams)
        out: list[tuple[int, int, float]] = []
        for gram, count in counts.items():
            bucket, sign = _hash_bucket(gram, self.dim)
            out.append((bucket, sign, count / n))
        return out


@dataclass
class CatalogVector:
    code: str
    tipo: str
    folded: str
    vec: dict[int, float]


class CatalogKnn:
    def __init__(self, rows: list[tuple[str, str, str]]) -> None:
        docs = [folded for _code, folded, _tipo in rows if folded]
        self.embedder = HashEmbedder()
        self.embedder.fit(docs)
        self.vectors: list[CatalogVector] = []
        seen: set[tuple[str, str]] = set()
        for code, folded, tipo in rows:
            if not folded or not code:
                continue
            key = (code, tipo)
            if key in seen:
                continue
            seen.add(key)
            self.vectors.append(
                CatalogVector(code, tipo, folded, self.embedder.embed(folded))
            )

    def query(self, folded: str, kind: str) -> tuple[CatalogVector | None, float, float]:
        if not folded or not self.vectors:
            return None, 0.0, 0.0
        vec = self.embedder.embed(folded)
        scored: list[tuple[float, CatalogVector]] = []
        for row in self.vectors:
            if kind == "S" and row.tipo != "S":
                continue
            if kind == "M" and row.tipo != "M":
                continue
            scored.append((_cosine(vec, row.vec), row))
        if not scored:
            return None, 0.0, 0.0
        scored.sort(key=lambda x: x[0], reverse=True)
        top1 = scored[0][0]
        top2 = scored[1][0] if len(scored) > 1 else 0.0
        return scored[0][1], top1, top2


def description_hash(folded: str) -> str:
    return hashlib.sha256(folded.encode("utf-8")).hexdigest()


def assign_knn(top1: float, top2: float) -> bool:
    return top1 >= KNN_COSINE_MIN and (top1 - top2) >= KNN_MARGIN_MIN


def llm_hook_enabled() -> bool:
    raw = os.environ.get(_LLM_FLAG, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def llm_hook_blocked() -> bool:
    if os.environ.get("COMPRAS_E2E", "").strip() == "1":
        return True
    if os.environ.get("CLASSIFIER_FIXTURE", "").strip() == "1":
        return True
    return False


def optional_llm_classify(_folded: str) -> KnnScore | None:
    """Optional hook. Default off. Never invents a code. Never called in fixture or e2e."""
    if not llm_hook_enabled() or llm_hook_blocked():
        return None
    return None


def _char_ngrams(text: str, widths: tuple[int, ...]) -> list[str]:
    key = fold(text)
    if not key:
        return []
    padded = f" {key} "
    out: list[str] = []
    for n in widths:
        if len(padded) < n:
            continue
        out.extend(padded[i : i + n] for i in range(len(padded) - n + 1))
    return out


def _hash_bucket(gram: str, dim: int) -> tuple[int, int]:
    digest = hashlib.sha256(gram.encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "little") % dim
    sign = 1 if digest[4] % 2 == 0 else -1
    return bucket, sign


def _l2_normalize(vec: dict[int, float]) -> dict[int, float]:
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm == 0:
        return {}
    return {k: v / norm for k, v in vec.items()}


def _cosine(a: dict[int, float], b: dict[int, float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    dot = 0.0
    for k, v in a.items():
        w = b.get(k)
        if w is not None:
            dot += v * w
    if dot < 0:
        return 0.0
    if dot > 1:
        return 1.0
    return dot
