from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import urlparse

import polars as pl

from compras_detect.tier1.common import flag, to_frame
from compras_normalize.text import fold

KIND = "cnae_mismatch"
TABLE_VERSION = "1"
_DATA = Path(__file__).resolve().parents[1] / "data"
ALLOW_PATH = _DATA / "catmat_cnae_allowlist.csv"
_CLASS_PATH = _DATA / "catalog_class.csv"
OFFICIAL_HOSTS = (
    "catalogo.compras.gov.br",
    "catalogo.gov.br",
    "compras.gov.br",
    "gov.br",
    "concla.ibge.gov.br",
    "ibge.gov.br",
)
_SPLIT = re.compile(r"[,;|/]+")


def detect_cnae_mismatch(items: pl.DataFrame) -> pl.DataFrame:
    allow = load_allowlist()
    classes = load_class_map()
    rows: list[dict] = []
    for row in items.iter_rows(named=True):
        if _is_service(row):
            continue
        classe = _catmat_class(row, classes)
        if not classe:
            continue
        prefixes = allow.get(classe)
        if not prefixes:
            continue
        cnaes = _winner_cnaes(row)
        if not cnaes:
            continue
        if any(_prefix_hit(code, prefixes) for code in cnaes):
            continue
        primary = cnaes[0]
        secondary = ",".join(cnaes[1:])
        rows.append(
            flag(
                row,
                KIND,
                (
                    f"indicio CATMAT class outside winner CNAE allow-list. "
                    f"class={classe} cnae={primary} secondary={secondary} "
                    f"allowed={','.join(prefixes)} table={TABLE_VERSION}"
                ),
            )
        )
    return to_frame(rows)


def load_allowlist(path: Path | None = None) -> dict[str, list[str]]:
    src = path or ALLOW_PATH
    out: dict[str, list[str]] = {}
    with src.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            version = str(row.get("version") or "").strip()
            if version != TABLE_VERSION:
                raise ValueError(f"allow-list version {version!r} is not {TABLE_VERSION}")
            classe = _digits(row.get("codigo_classe"))
            if len(classe) != 4:
                raise ValueError(f"allow-list class is not 4 digits: {row.get('codigo_classe')}")
            prefixes = _prefixes(row.get("allowed_prefixes"))
            if not prefixes:
                raise ValueError(f"allow-list class {classe} has no prefixes")
            _assert_official_url(str(row.get("catmat_source") or ""))
            _assert_official_url(str(row.get("cnae_source") or ""))
            out[classe] = prefixes
    return out


def load_class_map(path: Path | None = None) -> dict[str, tuple[str, str]]:
    paths = [path or _CLASS_PATH]
    paths.extend(_catalog_fixture_csvs())
    out: dict[str, tuple[str, str]] = {}
    for src in paths:
        if src is None or not src.is_file():
            continue
        with src.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh, delimiter=";"):
                folded = {fold(k).replace(" ", "").replace("_", ""): v for k, v in row.items()}
                code = _digits(folded.get("codigo") or folded.get("coditemcatalogo"))
                if not code:
                    continue
                classe = _digits(folded.get("codigoclasse") or folded.get("classe"))
                grupo = str(folded.get("codigogrupo") or folded.get("grupo") or "").strip()
                if classe or grupo:
                    out[code] = (classe, grupo)
    return out


def _is_service(row: dict) -> bool:
    tipo = str(row.get("material_ou_servico") or "").upper()[:1]
    if tipo == "S":
        return True
    catser = str(row.get("catser") or "").strip()
    catmat = str(row.get("catmat") or "").strip()
    return bool(catser) and not catmat


def _catmat_class(row: dict, classes: dict[str, tuple[str, str]]) -> str:
    classe = _digits(row.get("codigo_classe"))
    if len(classe) >= 4:
        return classe[:4]
    code = _digits(row.get("catmat"))
    mapped = classes.get(code) if code else None
    if mapped:
        map_classe = _digits(mapped[0])
        if len(map_classe) >= 4:
            return map_classe[:4]
    return ""


def _winner_cnaes(row: dict) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for key in ("cnae", "cnae_fiscal_principal", "cnae_secundaria", "cnae_fiscal_secundaria"):
        raw = str(row.get(key) or "")
        for part in _SPLIT.split(raw):
            digits = _digits(part)
            if not digits or digits in seen:
                continue
            seen.add(digits)
            out.append(digits)
    return out


def _prefix_hit(cnae: str, prefixes: list[str]) -> bool:
    return any(cnae.startswith(prefix) for prefix in prefixes)


def _prefixes(raw: object) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for part in _SPLIT.split(str(raw or "")):
        digits = _digits(part)
        if not digits:
            continue
        if len(digits) not in {2, 5}:
            raise ValueError(f"allow-list prefix must be 2 or 5 digits: {part}")
        if digits in seen:
            continue
        seen.add(digits)
        out.append(digits)
    return out


def _assert_official_url(url: str) -> None:
    host = (urlparse(url).hostname or "").lower()
    if not any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS):
        raise ValueError(f"allow-list url host is not official: {url}")


def _catalog_fixture_csvs() -> list[Path]:
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "ingest" / "fixtures" / "catalogo_cnbs"
        if cand.is_dir():
            return sorted(cand.glob("*.csv"))
    return []


def _digits(value: object) -> str:
    return "".join(c for c in str(value or "") if c.isdigit())
