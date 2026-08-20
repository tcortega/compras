from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from compras_ingest.landing import LandingRef, LandingStore, partition_date_of
from compras_ingest.settings import Settings
from compras_normalize.text import parse_datetime


def land_ocds(
    settings: Settings,
    compras_ids: set[str] | None = None,
    store: LandingStore | None = None,
) -> tuple[LandingRef, dict]:
    store = store or LandingStore(settings)
    path = settings.ocds_path
    if path is None:
        raise FileNotFoundError("OCDS_PATH missing. OCDS is a schema cross-check, not a primary source.")
    rows = _load_jsonl(path)
    df = pl.DataFrame(rows) if rows else pl.DataFrame({"ocid": []})
    dates = [parse_datetime(r.get("date")) for r in rows]
    ref = store.write_parquet("ocds", partition_date_of(dates), df if not df.is_empty() else pl.DataFrame({"ocid": []}))
    report = _crosscheck(rows, compras_ids or set())
    store.put(
        f"ocds/date={ref.partition_date}/{ref.sha256}.crosscheck.json",
        json.dumps(report, indent=2).encode(),
    )
    return ref, report


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        tender = obj.get("tender") or {}
        rows.append(
            {
                "ocid": str(obj.get("ocid") or ""),
                "id": str(obj.get("id") or ""),
                "date": str(obj.get("date") or ""),
                "tag": ",".join(obj.get("tag") or []),
                "tender_id": str(tender.get("id") or ""),
                "tender_title": str(tender.get("title") or tender.get("description") or ""),
                "has_tender": "tender" in obj,
                "has_awards": bool(obj.get("awards")),
                "schema_ok": _schema_ok(obj),
            }
        )
    return rows


def _schema_ok(obj: dict) -> bool:
    return bool(obj.get("ocid") and obj.get("id") and obj.get("date") and obj.get("tag"))


def _crosscheck(rows: list[dict], compras_ids: set[str]) -> dict:
    ocids = {r["ocid"] for r in rows if r["ocid"]}
    stripped = set()
    for ocid in ocids:
        stripped.add(ocid)
        if ocid.startswith("ocds-914jxj-"):
            stripped.add(ocid.removeprefix("ocds-914jxj-"))
    matched = {c for c in compras_ids if c in stripped or f"ocds-914jxj-{c}" in ocids}
    return {
        "role": "schema_crosscheck",
        "primary": False,
        "ocds_n": len(ocids),
        "compras_n": len(compras_ids),
        "matched_n": len(matched),
        "schema_ok_n": sum(1 for r in rows if r["schema_ok"]),
        "schema_bad_n": sum(1 for r in rows if not r["schema_ok"]),
    }
