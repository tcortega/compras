from __future__ import annotations

import gzip
import json
import tempfile
from pathlib import Path

import polars as pl

from compras_ingest.landing import LandingRef, LandingStore, partition_date_of
from compras_ingest.official import (
    OCDS_HOSTS,
    OcdsOfficial,
    download_to,
    http_client,
    resolve_ocds_feed,
)
from compras_ingest.settings import Settings
from compras_normalize.text import parse_datetime

OCDS_COLS = [
    "ocid",
    "id",
    "date",
    "tag",
    "tender_id",
    "tender_title",
    "has_tender",
    "has_awards",
    "schema_ok",
]


def land_ocds(
    settings: Settings,
    compras_ids: set[str] | None = None,
    store: LandingStore | None = None,
) -> tuple[LandingRef, dict]:
    store = store or LandingStore(settings)
    official = resolve_ocds_feed(settings.ocds_year)
    rows = load_ocds(settings, compras_ids, official)
    df = pl.DataFrame(rows, schema=OCDS_COLS) if rows else pl.DataFrame(schema=_empty_schema())
    dates = [parse_datetime(r.get("date")) for r in rows]
    ref = store.write_parquet("ocds", partition_date_of(dates), df)
    report = _crosscheck(rows, compras_ids or set())
    report["ocp_registry_url"] = official.registry_url
    report["ocp_jsonl_url"] = official.jsonl_url
    report["mode"] = "fetch" if settings.ocds_fetch else "fixture"
    store.put(
        f"ocds/date={ref.partition_date}/{ref.sha256}.crosscheck.json",
        json.dumps(report, indent=2).encode(),
    )
    return ref, report


def load_ocds(
    settings: Settings,
    compras_ids: set[str] | None = None,
    official: OcdsOfficial | None = None,
) -> list[dict]:
    if settings.ocds_fetch:
        official = official or resolve_ocds_feed(settings.ocds_year)
        return _fetch_ocp_jsonl(official, compras_ids)
    path = settings.ocds_path
    if path is None:
        raise FileNotFoundError("OCDS_PATH missing and OCDS_FETCH is off")
    return _load_jsonl(path)


def _fetch_ocp_jsonl(official: OcdsOfficial, compras_ids: set[str] | None) -> list[dict]:
    rows: list[dict] = []
    with http_client(timeout=180.0) as client, tempfile.NamedTemporaryFile(suffix=".jsonl.gz") as tmp:
        download_to(client, official.jsonl_url, tmp, OCDS_HOSTS)
        with gzip.open(tmp.name, "rt", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = _row_from_obj(json.loads(line))
                if compras_ids and not _matches_compras(row, compras_ids):
                    continue
                rows.append(row)
    return rows


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(_row_from_obj(json.loads(line)))
    return rows


def _row_from_obj(obj: dict) -> dict:
    tender = obj.get("tender") or {}
    return {
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


def _schema_ok(obj: dict) -> bool:
    return bool(obj.get("ocid") and obj.get("id") and obj.get("date") and obj.get("tag"))


def _matches_compras(row: dict, compras_ids: set[str]) -> bool:
    ocid = row["ocid"]
    if ocid in compras_ids:
        return True
    if ocid.startswith("ocds-914jxj-") and ocid.removeprefix("ocds-914jxj-") in compras_ids:
        return True
    return any(ocid.endswith(c) or f"ocds-914jxj-{c}" == ocid for c in compras_ids)


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


def _empty_schema() -> dict:
    return {
        "ocid": pl.String,
        "id": pl.String,
        "date": pl.String,
        "tag": pl.String,
        "tender_id": pl.String,
        "tender_title": pl.String,
        "has_tender": pl.Boolean,
        "has_awards": pl.Boolean,
        "schema_ok": pl.Boolean,
    }
