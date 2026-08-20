from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import polars as pl

from compras_ingest.cpf import assert_no_raw_cpf, is_cnpj, is_cpf, mask_cpf
from compras_ingest.csvio import read_csv
from compras_normalize.text import fold, parse_decimal

# Screens stay internal. Framing is indicio a verificar. Not a finding by itself.
KIND_EDGE = "co_bid"
KIND_VARIANCE = "bid_variance"
KIND_SKEW = "skew"
KIND_COVER = "cover_bidding"
KIND_ROTATION = "winner_rotation"
SCREEN_KINDS = (KIND_VARIANCE, KIND_SKEW, KIND_COVER, KIND_ROTATION)
ALLOWED_UF = frozenset({"SP", "RS"})
ALLOWED_SOURCE = frozenset({"tce_sp", "tce_rs"})
FRAMING = "indicio a verificar"
THRESH_PATH = Path(__file__).resolve().parent / "data" / "cade_screens.csv"
PLANTED_IDS = frozenset(
    {"COVER", "ROTATION", "VARIANCE", "SKEW", "CLEAN", "OTHER-UF", "CPFONLY"}
)

PART_SCHEMA = {
    "licitacaoId": pl.String,
    "uf": pl.String,
    "orgao": pl.String,
    "classe": pl.String,
    "itemLote": pl.String,
    "participante": pl.String,
    "proposta": pl.String,
    "winner": pl.Boolean,
    "source": pl.String,
    "plantedId": pl.String,
    "snapshot_id": pl.String,
    "methodology_version": pl.String,
}

EDGE_SCHEMA = {
    "kind": pl.String,
    "leftCnpj": pl.String,
    "rightCnpj": pl.String,
    "licitacaoId": pl.String,
    "itemLote": pl.String,
    "leftProposta": pl.String,
    "rightProposta": pl.String,
    "winner": pl.String,
    "snapshot_id": pl.String,
    "methodology_version": pl.String,
}

SCREEN_SCHEMA = {
    "kind": pl.String,
    "subjectId": pl.String,
    "licitacaoId": pl.String,
    "state": pl.String,
    "evidence": pl.String,
    "snapshot_id": pl.String,
    "methodology_version": pl.String,
}


def load_thresholds(path: Path | None = None) -> dict[tuple[str, str], Decimal]:
    """Versioned CADE screen knobs. No CADE/TCU published numeric cutoff found."""
    src = path or THRESH_PATH
    out: dict[tuple[str, str], Decimal] = {}
    with src.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            kind = str(row["kind"]).strip()
            param = str(row["param"]).strip()
            value = parse_decimal(row["value"])
            if value is None:
                raise ValueError(f"cade_screens missing value for {kind}.{param}")
            out[(kind, param)] = value
    return out


def fixture_dir(root: Path | None = None) -> Path:
    base = root or _repo_root()
    path = base / "detect" / "fixtures" / "cobid"
    if not path.exists():
        raise FileNotFoundError(f"cobid golden fixture missing: {path}")
    return path


def load_expected(root: Path | None = None) -> dict:
    path = fixture_dir(root) / "expected.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("cobid expected.json is not an object")
    return payload


def load_planted_participants(root: Path | None = None) -> pl.DataFrame:
    path = fixture_dir(root) / "participants.csv"
    return read_csv(path)


def normalize_participants(
    rows: pl.DataFrame,
    snapshot_id: str,
    methodology_version: str,
) -> pl.DataFrame:
    """Keep SP/RS + tce_sp/tce_rs only. Mask CPF. Drop OTHER UF and unknown sources."""
    snap = str(snapshot_id or "")
    meth = str(methodology_version or "")
    out: list[dict] = []
    for row in _as_rows(rows):
        source = _source(row.get("source"))
        uf = str(row.get("uf") or "").strip().upper()
        lid = str(row.get("licitacaoId") or row.get("licitacao_id") or "").strip()
        if source not in ALLOWED_SOURCE or uf not in ALLOWED_UF or not lid:
            continue
        token = _participant_token(row.get("participante"))
        if not token:
            continue
        assert_no_raw_cpf([token])
        planted = str(row.get("plantedId") or row.get("planted_id") or "").strip()
        out.append(
            {
                "licitacaoId": lid,
                "uf": uf,
                "orgao": str(row.get("orgao") or ""),
                "classe": str(row.get("classe") or ""),
                "itemLote": str(row.get("itemLote") or row.get("item_lote") or ""),
                "participante": token,
                "proposta": _dec_text(parse_decimal(row.get("proposta"))),
                "winner": _as_bool(row.get("winner")),
                "source": source,
                "plantedId": planted,
                "snapshot_id": str(row.get("snapshot_id") or row.get("snapshotId") or snap),
                "methodology_version": str(
                    row.get("methodology_version") or row.get("methodologyVersion") or meth
                ),
            }
        )
    return pl.DataFrame(out) if out else pl.DataFrame(schema=PART_SCHEMA)


def extract_tce_sp(df: pl.DataFrame, snapshot_id: str, methodology_version: str) -> pl.DataFrame:
    if df is None or df.is_empty():
        return pl.DataFrame(schema=PART_SCHEMA)
    cols = _fold_cols(df)
    lic = _need(cols, "codigo da licitacao")
    orgao = _need(cols, "entidade")
    item = cols.get("produto (item)") or cols.get("produto") or ""
    part = _need(cols, "cnpj do participante candidato")
    proposta = _need(cols, "valor da proposta")
    result = _need(cols, "resultado da habilitacao")
    objeto = cols.get("objeto") or ""
    rows = []
    for row in df.iter_rows(named=True):
        rows.append(
            {
                "licitacaoId": str(row.get(lic) or ""),
                "uf": "SP",
                "orgao": str(row.get(orgao) or ""),
                "classe": fold(row.get(objeto) if objeto else ""),
                "itemLote": str(row.get(item) or "") if item else "",
                "participante": row.get(part),
                "proposta": row.get(proposta),
                "winner": "vencedor" in fold(row.get(result)),
                "source": "tce_sp",
                "plantedId": "",
                "snapshot_id": snapshot_id,
                "methodology_version": methodology_version,
            }
        )
    return normalize_participants(pl.DataFrame(rows), snapshot_id, methodology_version)


def extract_tce_rs(df: pl.DataFrame, snapshot_id: str, methodology_version: str) -> pl.DataFrame:
    if df is None or df.is_empty() or "_table" not in df.columns:
        return pl.DataFrame(schema=PART_SCHEMA)
    by_table: dict[str, list[dict]] = defaultdict(list)
    for row in df.iter_rows(named=True):
        by_table[str(row.get("_table") or "")].append(row)
    winners = _rs_winners(by_table)
    chosen: list[dict] = []
    for table in ("ITEM_PROPOSTA", "LOTE_PROPOSTA", "PROPOSTA"):
        have = {_rs_lic_id(r) for r in chosen}
        for row in by_table.get(table, ()):
            lid = _rs_lic_id(row)
            if not lid or lid in have:
                continue
            chosen.append(row)
    rows = []
    for row in chosen:
        lid = _rs_lic_id(row)
        doc = _rs_doc(row)
        lote = _rs_col(row, "nr_lote")
        item = _rs_col(row, "nr_item")
        item_lote = "/".join(p for p in (lote, item) if p)
        value = (
            _rs_col(row, "vl_total_item")
            or _rs_col(row, "vl_total_lote")
            or _rs_col(row, "vl_total_proposta")
        )
        orgao = _rs_col(row, "cd_orgao")
        rows.append(
            {
                "licitacaoId": lid,
                "uf": "RS",
                "orgao": orgao,
                "classe": _rs_col(row, "cd_tipo_modalidade"),
                "itemLote": item_lote,
                "participante": doc,
                "proposta": value,
                "winner": (lid, _digits(doc)) in winners or (lid, mask_cpf(str(doc or ""))) in winners,
                "source": "tce_rs",
                "plantedId": "",
                "snapshot_id": snapshot_id,
                "methodology_version": methodology_version,
            }
        )
    return normalize_participants(pl.DataFrame(rows) if rows else pl.DataFrame(), snapshot_id, methodology_version)


def build_cobid_edges(
    participants: pl.DataFrame,
    snapshot_id: str,
    methodology_version: str,
) -> pl.DataFrame:
    """Undirected co_bid edges. Not a finding."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in _as_rows(participants):
        lid = str(row.get("licitacaoId") or "")
        item = str(row.get("itemLote") or "")
        token = str(row.get("participante") or "")
        if not lid or not token:
            continue
        groups[(lid, item)].append(row)
    out: list[dict] = []
    seen: set[tuple[str, str, str, str]] = set()
    for (lid, item), members in groups.items():
        ordered = sorted(members, key=lambda r: str(r.get("participante") or ""))
        for i, left in enumerate(ordered):
            for right in ordered[i + 1 :]:
                a = str(left.get("participante") or "")
                b = str(right.get("participante") or "")
                if not a or not b or a == b:
                    continue
                if a > b:
                    left, right = right, left
                    a, b = b, a
                key = (a, b, lid, item)
                if key in seen:
                    continue
                seen.add(key)
                win = ""
                if _as_bool(left.get("winner")):
                    win = a
                elif _as_bool(right.get("winner")):
                    win = b
                out.append(
                    {
                        "kind": KIND_EDGE,
                        "leftCnpj": a,
                        "rightCnpj": b,
                        "licitacaoId": lid,
                        "itemLote": item,
                        "leftProposta": _dec_text(parse_decimal(left.get("proposta"))),
                        "rightProposta": _dec_text(parse_decimal(right.get("proposta"))),
                        "winner": win,
                        "snapshot_id": str(left.get("snapshot_id") or snapshot_id),
                        "methodology_version": str(left.get("methodology_version") or methodology_version),
                    }
                )
    return pl.DataFrame(out) if out else pl.DataFrame(schema=EDGE_SCHEMA)


def detect_cade_screens(
    participants: pl.DataFrame,
    snapshot_id: str,
    methodology_version: str,
    thresholds: dict[tuple[str, str], Decimal] | None = None,
) -> pl.DataFrame:
    """Internal CADE screens. SP/RS warehouse rows only. state=detected."""
    thresh = thresholds or load_thresholds()
    rows = [r for r in _as_rows(participants) if r.get("source") in ALLOWED_SOURCE]
    by_event: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        lid = str(row.get("licitacaoId") or "")
        if not lid:
            continue
        by_event[(lid, str(row.get("itemLote") or ""))].append(row)
    found: list[dict] = []
    found.extend(_variance_screens(by_event, thresh, snapshot_id, methodology_version))
    found.extend(_skew_screens(by_event, thresh, snapshot_id, methodology_version))
    found.extend(_cover_screens(by_event, thresh, snapshot_id, methodology_version))
    found.extend(_rotation_screens(rows, thresh, snapshot_id, methodology_version))
    return pl.DataFrame(found) if found else pl.DataFrame(schema=SCREEN_SCHEMA)


def subject_id(row: dict) -> str:
    planted = str(row.get("plantedId") or "").strip()
    if planted:
        return planted
    lid = str(row.get("licitacaoId") or "")
    if "-" in lid:
        head = lid.split("-", 1)[0]
        if head in PLANTED_IDS:
            return head
    return lid


def _variance_screens(by_event, thresh, snap, meth) -> list[dict]:
    # bid_variance: unusually tight proposed values among 3+ bidders on one item/lote.
    # Stat: sample CV = s / mean, s = sqrt(sum((x-mean)^2) / (n-1)).
    # Flag iff n >= min_bidders and CV <= max_cv.
    # CADE cartilha / TCU bid-rigging notes describe "propostas proximas" with no numeric cutoff.
    # Threshold lives in cade_screens.csv. Internal heuristic. Not a legal test.
    min_n = int(thresh[(KIND_VARIANCE, "min_bidders")])
    max_cv = thresh[(KIND_VARIANCE, "max_cv")]
    out = []
    for (lid, item), members in by_event.items():
        values = _bid_values(members)
        if len(values) < min_n:
            continue
        cv = _cv(values)
        if cv is None or cv > max_cv:
            continue
        out.append(
            _screen(
                KIND_VARIANCE,
                members,
                lid,
                {
                    "rule": "sample_cv",
                    "n": len(values),
                    "cv": str(cv),
                    "max_cv": str(max_cv),
                    "itemLote": item,
                    "values": [str(v) for v in values],
                },
                snap,
                meth,
            )
        )
    return out


def _skew_screens(by_event, thresh, snap, meth) -> list[dict]:
    # skew: one bid far below a tight cluster of the others (cover pattern).
    # Stat: unique minimum vs the remaining bids. Cluster n >= min_cluster (so total n >= 4).
    # Flag iff cluster sample CV <= cluster_max_cv and (min / cluster_median) <= max_low_ratio.
    # No CADE/TCU numeric cutoff. Internal heuristic. Not a legal test.
    min_cluster = int(thresh[(KIND_SKEW, "min_cluster")])
    max_cv = thresh[(KIND_SKEW, "cluster_max_cv")]
    max_ratio = thresh[(KIND_SKEW, "max_low_ratio")]
    out = []
    for (lid, item), members in by_event.items():
        valued = [(parse_decimal(r.get("proposta")), r) for r in members]
        valued = [(v, r) for v, r in valued if v is not None]
        if len(valued) < min_cluster + 1:
            continue
        low = min(v for v, _ in valued)
        lows = [r for v, r in valued if v == low]
        if len(lows) != 1:
            continue
        cluster = [v for v, _ in valued if v != low]
        if len(cluster) < min_cluster:
            continue
        cv = _cv(cluster)
        med = _median(cluster)
        if cv is None or med is None or med == 0 or cv > max_cv:
            continue
        ratio = (low / med).quantize(Decimal("0.0001"))
        if ratio > max_ratio:
            continue
        out.append(
            _screen(
                KIND_SKEW,
                members,
                lid,
                {
                    "rule": "low_vs_tight_cluster",
                    "low": str(low),
                    "cluster_n": len(cluster),
                    "cluster_cv": str(cv),
                    "cluster_median": str(med),
                    "low_ratio": str(ratio),
                    "max_low_ratio": str(max_ratio),
                    "itemLote": item,
                },
                snap,
                meth,
            )
        )
    return out


def _cover_screens(by_event, thresh, snap, meth) -> list[dict]:
    # cover_bidding: planted high complementary bids that lose, same pair repeats.
    # Event = one (licitacaoId, itemLote). Pair must both bid.
    # Complementary iff max/min >= min_ratio and the higher never wins any shared event.
    # Flag iff such events >= min_repeats. Subject is plantedId or first licitacao.
    # No CADE/TCU numeric cutoff. Internal heuristic. Not a legal test.
    min_repeats = int(thresh[(KIND_COVER, "min_repeats")])
    min_ratio = thresh[(KIND_COVER, "min_ratio")]
    pair_events: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for (lid, item), members in by_event.items():
        cnpjs = [r for r in members if is_cnpj(str(r.get("participante") or ""))]
        for i, left in enumerate(cnpjs):
            for right in cnpjs[i + 1 :]:
                a = str(left["participante"])
                b = str(right["participante"])
                va = parse_decimal(left.get("proposta"))
                vb = parse_decimal(right.get("proposta"))
                if va is None or vb is None or va == 0 or vb == 0:
                    continue
                high, low = (left, right) if va >= vb else (right, left)
                hi_v, lo_v = (va, vb) if va >= vb else (vb, va)
                ratio = (hi_v / lo_v).quantize(Decimal("0.0001"))
                if ratio < min_ratio:
                    continue
                if _as_bool(high.get("winner")):
                    continue
                key = (a, b) if a < b else (b, a)
                pair_events[key].append(
                    {
                        "licitacaoId": lid,
                        "itemLote": item,
                        "high": str(high["participante"]),
                        "low": str(low["participante"]),
                        "high_value": str(hi_v),
                        "low_value": str(lo_v),
                        "ratio": str(ratio),
                        "high_won": False,
                        "members": members,
                    }
                )
    out = []
    seen: set[str] = set()
    for pair, events in pair_events.items():
        if len(events) < min_repeats:
            continue
        highs = {e["high"] for e in events}
        if len(highs) != 1:
            continue
        if any(e["high_won"] for e in events):
            continue
        members = events[0]["members"]
        subject = subject_id(members[0])
        if subject in seen:
            continue
        seen.add(subject)
        out.append(
            _screen(
                KIND_COVER,
                members,
                events[0]["licitacaoId"],
                {
                    "rule": "repeat_complementary_loser",
                    "leftCnpj": pair[0],
                    "rightCnpj": pair[1],
                    "n": len(events),
                    "min_repeats": min_repeats,
                    "min_ratio": str(min_ratio),
                    "high": events[0]["high"],
                    "licitacoes": [e["licitacaoId"] for e in events],
                },
                snap,
                meth,
                subject=subject,
            )
        )
    return out


def _rotation_screens(rows, thresh, snap, meth) -> list[dict]:
    # winner_rotation: same small set of CNPJs rotate wins across related licitacoes.
    # Group = (orgao, classe). Only winner CNPJs count.
    # Flag iff n_licitacoes >= min_licitacoes, unique winners in [min_set, max_set],
    # every winner wins at least once, and the set is closed (no outsider win).
    # Planted ROTATION is 3 licitacoes / 3 winners / 1 each.
    # No CADE/TCU numeric cutoff. Internal heuristic. Not a legal test.
    min_set = int(thresh[(KIND_ROTATION, "min_set")])
    max_set = int(thresh[(KIND_ROTATION, "max_set")])
    min_lic = int(thresh[(KIND_ROTATION, "min_licitacoes")])
    grouped: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    members_by_group: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if not is_cnpj(str(row.get("participante") or "")):
            continue
        members_by_group[(str(row.get("orgao") or ""), str(row.get("classe") or ""))].append(row)
        if not _as_bool(row.get("winner")):
            continue
        lid = str(row.get("licitacaoId") or "")
        if not lid:
            continue
        grouped[(str(row.get("orgao") or ""), str(row.get("classe") or ""))][lid] = str(
            row["participante"]
        )
    out = []
    for key, wins in grouped.items():
        if len(wins) < min_lic:
            continue
        winners = set(wins.values())
        if not (min_set <= len(winners) <= max_set):
            continue
        if len(winners) < min_set:
            continue
        counts = defaultdict(int)
        for w in wins.values():
            counts[w] += 1
        if any(c < 1 for c in counts.values()):
            continue
        if max(counts.values()) >= len(wins):
            continue
        members = members_by_group[key]
        subject = subject_id(members[0]) if members else next(iter(wins))
        out.append(
            _screen(
                KIND_ROTATION,
                members,
                next(iter(wins)),
                {
                    "rule": "closed_set_rotation",
                    "orgao": key[0],
                    "classe": key[1],
                    "n": len(wins),
                    "winners": sorted(winners),
                    "win_counts": dict(counts),
                    "licitacoes": sorted(wins),
                },
                snap,
                meth,
                subject=subject,
            )
        )
    return out


def _screen(kind, members, licitacao_id, extra, snap, meth, subject=None) -> dict:
    row = members[0] if members else {}
    payload = {
        "framing": FRAMING,
        "kind": kind,
        "uf": str(row.get("uf") or ""),
        "source": str(row.get("source") or ""),
        **extra,
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    assert_no_raw_cpf([blob])
    return {
        "kind": kind,
        "subjectId": subject or subject_id(row),
        "licitacaoId": licitacao_id,
        "state": "detected",
        "evidence": blob,
        "snapshot_id": str(row.get("snapshot_id") or snap),
        "methodology_version": str(row.get("methodology_version") or meth),
    }


def _bid_values(members: list[dict]) -> list[Decimal]:
    values = []
    for row in members:
        parsed = parse_decimal(row.get("proposta"))
        if parsed is not None:
            values.append(parsed)
    return values


def _cv(values: list[Decimal]) -> Decimal | None:
    if len(values) < 2:
        return None
    mean = sum(values) / Decimal(len(values))
    if mean == 0:
        return None
    var = sum((v - mean) ** 2 for v in values) / Decimal(len(values) - 1)
    std = Decimal(str(math.sqrt(float(var))))
    return (std / mean).quantize(Decimal("0.0001"))


def _median(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / Decimal(2)


def _participant_token(value) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    masked = mask_cpf(raw)
    digits = _digits(raw)
    if is_cnpj(raw) or len(digits) == 14:
        return digits
    if is_cpf(raw) or _masked_cpf(masked):
        return masked if _masked_cpf(masked) else mask_cpf(digits)
    return ""


def _source(value) -> str:
    raw = fold(value).replace("-", "_").replace(" ", "_")
    if raw in {"tce_sp", "tce_sp_licitacao"}:
        return "tce_sp"
    if raw in {"tce_rs", "tce_rs_licitacon"}:
        return "tce_rs"
    return raw


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return fold(value) in {"1", "true", "t", "yes", "vencedor"}


def _dec_text(value: Decimal | None) -> str:
    return str(value) if value is not None else ""


def _digits(value) -> str:
    return "".join(c for c in str(value or "") if c.isdigit())


def _masked_cpf(value: str) -> bool:
    return value.startswith("***") and "-" in value


def _fold_cols(df: pl.DataFrame) -> dict[str, str]:
    return {fold(c): c for c in df.columns}


def _need(cols: dict[str, str], name: str) -> str:
    key = fold(name)
    if key not in cols:
        raise RuntimeError(f"missing column {name}")
    return cols[key]


def _rs_col(row: dict, name: str) -> str:
    want = fold(name).replace(" ", "_")
    for key, value in row.items():
        if fold(key).replace(" ", "_") == want:
            return str(value or "").strip()
    return ""


def _rs_lic_id(row: dict) -> str:
    nr = _rs_col(row, "nr_licitacao")
    ano = _rs_col(row, "ano_licitacao")
    mod = _rs_col(row, "cd_tipo_modalidade")
    if not nr:
        return ""
    return "/".join(p for p in (nr, ano, mod) if p)


def _rs_doc(row: dict) -> str:
    return _rs_col(row, "nr_documento_licitante") or _rs_col(row, "nr_documento_vencedor")


def _rs_winners(by_table: dict[str, list[dict]]) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for table in ("ITEM", "LOTE", "LICITACAO"):
        for row in by_table.get(table, ()):
            lid = _rs_lic_id(row)
            doc = _rs_col(row, "nr_documento_vencedor")
            token = _digits(doc) if len(_digits(doc)) == 14 else mask_cpf(doc)
            if lid and token:
                out.add((lid, token))
    return out


def _as_rows(df: pl.DataFrame) -> list[dict]:
    if df is None or df.is_empty():
        return []
    return list(df.iter_rows(named=True))


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "detect" / "fixtures").exists() and (p / "docs" / "CONTRACT.md").exists():
            return p
    return here.parents[2]
