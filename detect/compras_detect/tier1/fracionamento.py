from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

import polars as pl

from compras_detect.tier1.common import award_date, flag, to_frame
from compras_normalize.text import fold, parse_decimal

KIND_OVER = "fracionamento"
KIND_CLUSTER = "fracionamento_cluster"
CLUSTER_RATIO = Decimal("90") / Decimal("100")
CLUSTER_DAYS = 90
OFFICIAL_HOSTS = ("planalto.gov.br", "in.gov.br", "compras.gov.br", "gov.br")
_DATA = Path(__file__).resolve().parents[1] / "data"
THRESH_PATH = _DATA / "dispensa_thresholds.csv"
_CLASS_PATH = _DATA / "catalog_class.csv"


@dataclass
class Threshold:
    year: int
    kind: str
    amount: Decimal
    decree: str
    dou: str
    url: str


@dataclass
class Purchase:
    pid: str
    value: Decimal
    awarded: date | None
    items: list[dict] = field(default_factory=list)


def load_thresholds(path: Path | None = None) -> dict[tuple[int, str], Threshold]:
    src = path or THRESH_PATH
    out: dict[tuple[int, str], Threshold] = {}
    with src.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            year = int(str(row["year"]).strip())
            kind = str(row["kind"]).strip()
            if kind not in {"obras", "compras"}:
                raise ValueError(f"threshold kind is not obras|compras: {kind}")
            url = str(row["url"]).strip()
            _assert_official_url(url)
            amount = parse_decimal(row["amount"])
            if amount is None:
                raise ValueError(f"threshold amount missing for {year} {kind}")
            out[(year, kind)] = Threshold(
                year,
                kind,
                amount,
                str(row["decree"]).strip(),
                str(row["dou"]).strip(),
                url,
            )
    return out


def load_class_map(path: Path | None = None) -> dict[str, tuple[str, str]]:
    paths = [path or _CLASS_PATH]
    paths.extend(_catalog_fixture_csvs())
    out: dict[str, tuple[str, str]] = {}
    for src in paths:
        if src is None or not src.is_file():
            continue
        with src.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            for row in reader:
                folded = {fold(k).replace(" ", "").replace("_", ""): v for k, v in row.items()}
                code = "".join(c for c in str(folded.get("codigo") or folded.get("coditemcatalogo") or "") if c.isdigit())
                if not code:
                    continue
                classe = str(folded.get("codigoclasse") or folded.get("classe") or "").strip()
                grupo = str(folded.get("codigogrupo") or folded.get("grupo") or "").strip()
                if classe or grupo:
                    out[code] = (classe, grupo)
    return out


def detect_fracionamento(items: pl.DataFrame) -> pl.DataFrame:
    table = load_thresholds()
    classes = load_class_map()
    groups: dict[tuple[str, str, int], list[Purchase]] = defaultdict(list)
    group_rows: dict[tuple[str, str, int], list[dict]] = defaultdict(list)
    index: dict[tuple[str, str, int], dict[str, Purchase]] = defaultdict(dict)
    for row in items.iter_rows(named=True):
        if not _is_dispensa(row):
            continue
        orgao = str(row.get("orgao_cnpj") or "")
        class_key = _class_key(row, classes)
        year = _fiscal_year(row)
        if not orgao or not class_key or year is None:
            continue
        gkey = (orgao, class_key, year)
        pid = str(row.get("id_compra") or row.get("pncp_id") or row.get("record_id") or "")
        if not pid:
            continue
        value = _item_value(row)
        if value is None:
            continue
        found = index[gkey].get(pid)
        if found is None:
            found = Purchase(pid, Decimal("0"), award_date(row), [])
            index[gkey][pid] = found
            groups[gkey].append(found)
        found.value += value
        if found.awarded is None:
            found.awarded = award_date(row)
        found.items.append(row)
        group_rows[gkey].append(row)
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for (orgao, class_key, year), purchases in groups.items():
        kind = "obras" if _looks_obra(group_rows[(orgao, class_key, year)]) else "compras"
        thresh = table.get((year, kind))
        if thresh is None:
            continue
        cluster_ids = _cluster_purchase_ids(purchases, thresh.amount)
        over_ids = _over_sum_purchase_ids(purchases, thresh.amount)
        if cluster_ids:
            rule = "cluster"
            flag_kind = KIND_CLUSTER
            flagged = [p for p in purchases if p.pid in cluster_ids]
        elif over_ids:
            rule = "over_sum"
            flag_kind = KIND_OVER
            flagged = [p for p in purchases if p.pid in over_ids]
        else:
            continue
        n = len(flagged)
        total = sum((p.value for p in flagged), Decimal("0"))
        delta = (
            f"indicio Art. 75 par.1 same-object annual aggregate. "
            f"orgao={orgao} class_key={class_key} year={year} n={n} "
            f"sum={total} threshold={thresh.amount} decree={thresh.decree} "
            f"kind={kind} rule={rule}"
        )
        for purchase in flagged:
            for rec in purchase.items:
                rid = str(rec.get("record_id") or "")
                key = (rid, flag_kind)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(flag(rec, flag_kind, delta))
    return to_frame(rows)


def _assert_official_url(url: str) -> None:
    host = (urlparse(url).hostname or "").lower()
    if not any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS):
        raise ValueError(f"threshold url host is not official: {url}")


def _catalog_fixture_csvs() -> list[Path]:
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "ingest" / "fixtures" / "catalogo_cnbs"
        if cand.is_dir():
            return sorted(cand.glob("*.csv"))
    return []


def _is_dispensa(row: dict) -> bool:
    nome = fold(str(row.get("modalidade") or ""))
    codigo = str(row.get("modalidade_codigo") or "").strip()
    return codigo == "8" or "dispensa" in nome


def _looks_obra(recs: list[dict]) -> bool:
    blob = " ".join(fold(str(r.get("objeto") or "")) + " " + fold(str(r.get("descricao") or "")) for r in recs)
    return "obra" in blob or "engenharia" in blob


def _fiscal_year(row: dict) -> int | None:
    awarded = award_date(row)
    raw = str(awarded.year) if awarded else str(row.get("ano") or "")[:4]
    if len(raw) != 4 or not raw.isdigit():
        return None
    return int(raw)


def _item_value(row: dict) -> Decimal | None:
    return parse_decimal(row.get("valor_total")) or parse_decimal(row.get("valor_homologado"))


def _class_key(row: dict, classes: dict[str, tuple[str, str]]) -> str | None:
    classe = str(row.get("codigo_classe") or "").strip()
    if classe:
        return f"codigo_classe:{classe}"
    grupo = str(row.get("codigo_grupo") or "").strip()
    if grupo:
        return f"codigo_grupo:{grupo}"
    code = str(row.get("catmat") or row.get("catser") or "")
    digits = "".join(c for c in code if c.isdigit())
    mapped = classes.get(digits) if digits else None
    if mapped:
        map_classe, map_grupo = mapped
        if map_classe:
            return f"codigo_classe:{map_classe}"
        if map_grupo:
            return f"codigo_grupo:{map_grupo}"
    if len(digits) >= 6:
        return f"codigo_classe:{digits[:4]}"
    if digits or code.strip():
        return f"item:{digits or code.strip()}"
    return None


def _over_sum_purchase_ids(purchases: list[Purchase], threshold: Decimal) -> set[str]:
    if len(purchases) < 2:
        return set()
    if any(p.value >= threshold for p in purchases):
        return set()
    total = sum((p.value for p in purchases), Decimal("0"))
    if total <= threshold:
        return set()
    return {p.pid for p in purchases}


def _cluster_purchase_ids(purchases: list[Purchase], threshold: Decimal) -> set[str]:
    floor = (threshold * CLUSTER_RATIO)
    band = [p for p in purchases if p.awarded is not None and p.value >= floor and p.value < threshold]
    if len(band) < 3:
        return set()
    band.sort(key=lambda p: p.awarded or date.min)
    limit = timedelta(days=CLUSTER_DAYS)
    best: list[Purchase] = []
    end = 0
    for start, left in enumerate(band):
        if left.awarded is None:
            continue
        while end < len(band) and band[end].awarded is not None and band[end].awarded - left.awarded <= limit:
            end += 1
        window = band[start:end]
        if len(window) >= 3 and len(window) > len(best):
            best = window
    if len(best) < 3:
        return set()
    return {p.pid for p in best}
