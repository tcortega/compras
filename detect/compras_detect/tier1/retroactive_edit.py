from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import polars as pl

from compras_detect.tier1.common import flag, to_frame
from compras_normalize.text import fold, parse_date, parse_decimal

KIND = "retroactive_edit"

PRICE_FIELDS = {
    "valor_unitario_resultado": ("valorunitarioresultado",),
    "valor_unitario_estimado": ("valorunitarioestimado",),
    "valor_unitario_homologado": ("valorunitariohomologado",),
}
QTY_FIELDS = {
    "quantidade": ("quantidaderesultado", "quantidade", "quantidadehomologada"),
}
SUPPLIER_FIELDS = {
    "fornecedor_cnpj": ("codfornecedor", "nifornecedor", "fornecedorcnpj"),
    "fornecedor_razao": ("nomefornecedor", "nomerazaosocialfornecedor", "fornecedorrazao"),
}
PUB_KEYS = ("datapublicacaopncp", "publicadoem")
AWARD_KEYS = ("dataresultado", "awarddate")
SNAP_DATE_KEYS = ("dataatualizacaopncp", "partitiondate", "_partition_date")


def detect_retroactive_edits(landing_records: pl.DataFrame | None) -> pl.DataFrame:
    if landing_records is None or landing_records.is_empty():
        return to_frame([])
    by_id: dict[str, list[dict]] = defaultdict(list)
    for row in landing_records.iter_rows(named=True):
        rid = str(row.get("record_id") or "")
        if rid:
            by_id[rid].append(row)
    rows: list[dict] = []
    for rid, recs in by_id.items():
        ordered = sorted(recs, key=_snap_sort_key)
        unique: list[dict] = []
        seen: set[str] = set()
        for rec in ordered:
            h = str(rec.get("record_hash") or "")
            if not h or h in seen:
                continue
            seen.add(h)
            unique.append(rec)
        if len(unique) < 2:
            continue
        gate = _gate_date(unique[-1]) or _gate_date(unique[0])
        hit = None
        for prev, curr in zip(unique, unique[1:]):
            if gate is None:
                continue
            curr_on = _snapshot_date(curr)
            if curr_on is None or curr_on <= gate:
                continue
            changed = _field_diffs(prev, curr)
            if not changed:
                continue
            hit = (prev, curr, changed)
        if hit is None:
            continue
        prev, curr, changed = hit
        payload = {
            "fields": changed,
            "old_hash": str(prev.get("record_hash") or ""),
            "new_hash": str(curr.get("record_hash") or ""),
            "old_snapshot_id": _snapshot_id(prev),
            "new_snapshot_id": _snapshot_id(curr),
        }
        out = dict(curr)
        out["record_id"] = rid
        out["pncp_id"] = _pncp_id(curr) or _pncp_id(prev)
        out["snapshot_id"] = _snapshot_id(curr)
        rows.append(flag(out, KIND, json.dumps(payload, ensure_ascii=False, sort_keys=True)))
    return to_frame(rows)


def fixture_dir(root: Path | None = None) -> Path:
    base = root or _repo_root()
    path = base / "detect" / "fixtures" / "retroactive_edit"
    if not path.exists():
        raise FileNotFoundError(f"retroactive_edit golden fixture missing: {path}")
    return path


def _folded(row: dict) -> dict:
    return {fold(str(k)).replace(" ", "").replace("_", ""): v for k, v in row.items()}


def _first(folded: dict, keys: tuple[str, ...]):
    for key in keys:
        if key in folded and folded[key] not in (None, ""):
            return folded[key]
    return None


def _gate_date(row: dict) -> date | None:
    folded = _folded(row)
    award = parse_date(_first(folded, AWARD_KEYS))
    pub = parse_date(_first(folded, PUB_KEYS))
    return award or pub


def _snapshot_date(row: dict) -> date | None:
    folded = _folded(row)
    return parse_date(_first(folded, SNAP_DATE_KEYS)) or parse_date(row.get("_partition_date"))


def _snapshot_id(row: dict) -> str:
    return str(row.get("snapshot_id") or row.get("_landing_sha256") or row.get("record_hash") or "")


def _pncp_id(row: dict) -> str:
    folded = _folded(row)
    return str(
        _first(folded, ("pncpid", "numerocontrolepncp", "idcontratacaopncp"))
        or row.get("pncp_id")
        or ""
    )


def _snap_sort_key(row: dict) -> tuple:
    on = _snapshot_date(row) or date.min
    return (on.isoformat(), _snapshot_id(row), str(row.get("record_hash") or ""))


def _field_diffs(prev: dict, curr: dict) -> dict[str, dict[str, str | None]]:
    before = _watched(prev)
    after = _watched(curr)
    out: dict[str, dict[str, str | None]] = {}
    for name in (*PRICE_FIELDS, *QTY_FIELDS, *SUPPLIER_FIELDS):
        if before[name] != after[name]:
            out[name] = {"before": before[name], "after": after[name]}
    return out


def _watched(row: dict) -> dict[str, str | None]:
    folded = _folded(row)
    out: dict[str, str | None] = {}
    for name, keys in PRICE_FIELDS.items():
        out[name] = _dec_str(_first(folded, keys))
    for name, keys in QTY_FIELDS.items():
        out[name] = _dec_str(_first(folded, keys))
    cnpj = _first(folded, SUPPLIER_FIELDS["fornecedor_cnpj"])
    digits = "".join(c for c in str(cnpj or "") if c.isdigit())
    out["fornecedor_cnpj"] = digits or None
    razao = _first(folded, SUPPLIER_FIELDS["fornecedor_razao"])
    out["fornecedor_razao"] = fold(str(razao)) if razao not in (None, "") else None
    return out


def _dec_str(value) -> str | None:
    parsed = parse_decimal(value)
    if parsed is None:
        return None
    return format(parsed, "f")


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "detect" / "fixtures").exists() and (p / "docs" / "CONTRACT.md").exists():
            return p
    return here.parents[3]
