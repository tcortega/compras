from __future__ import annotations

import sys
from pathlib import Path

from compras_detect.tier1 import run_tier1
from compras_ingest.cpf import assert_no_raw_cpf, mask_cpf
from compras_ingest.landing import LandingStore
from compras_ingest.official import (
    OCDS_OCP_REGISTRY_URL,
    RFB_SHARE_URL,
    resolve_ocds_feed,
    resolve_receita_index,
)
from compras_ingest.pipeline import _collect_landing_records, land_second_snapshot, run_compras_slice
from compras_ingest.settings import Settings
from compras_ingest.sources.ocds import land_ocds
from compras_ingest.sources.receita_cnpj import cnpj_basicos_from_frame, land_receita_cnpj
from compras_ingest.warehouse import fetch_contratacao, fetch_items_for, fetch_one_orgao, fetch_raw_text_blobs, write_flags


ORGAO_CNPJ = "29477000000180"
PNCP_ID = "29477000000180-1-2024-000001"
RAW_CPF = "12345678901"
LANDED_SOURCES = ("compras_gov", "ocds", "receita_cnpj", "receita_cnpj_socios")


def main() -> int:
    settings = Settings.from_env()
    _check_defs()
    official = _assert_official_urls(settings)
    result = run_compras_slice(settings)
    _assert_landing(settings, result.landing.sha256)
    _assert_tier_a_landing(settings, result.ocds_report)
    _assert_write_once(settings)
    orgao = fetch_one_orgao(settings, ORGAO_CNPJ)
    if orgao is None:
        raise SystemExit(f"missing orgao {ORGAO_CNPJ}")
    contratacao = fetch_contratacao(settings, PNCP_ID)
    if contratacao is None:
        raise SystemExit(f"missing contratacao {PNCP_ID}")
    items = fetch_items_for(settings, str(contratacao["id"]))
    if not items:
        raise SystemExit("missing item rows for contratacao")
    store = LandingStore(settings)
    mutate = str(result.items["record_id"][0])
    land_second_snapshot(settings, mutate, store)
    landing_records = _collect_landing_records(store, "compras_gov")
    flags = run_tier1(result.items, landing_records=landing_records, sanctions=None)
    write_flags(settings, flags, result.items)
    kinds = set(result.flags["kind"].to_list()) if result.flags.height else set()
    kinds.update(flags["kind"].to_list() if flags.height else [])
    if "qty_unit_price_neq_total" not in kinds:
        raise SystemExit("expected qty_unit_price_neq_total flag from fixture")
    if "retroactive_edit" not in kinds:
        raise SystemExit("expected retroactive_edit after second landing")
    blobs = fetch_raw_text_blobs(settings)
    for source in LANDED_SOURCES:
        for key in store.list_parquet(source):
            df = store.read_parquet(key)
            blobs.extend(str(v) for col in df.columns for v in df[col].to_list())
    assert_no_raw_cpf(blobs)
    if mask_cpf(RAW_CPF) not in " ".join(blobs):
        raise SystemExit("masked CPF not present in landing")
    print("e2e ok")
    print(f"landing={result.landing.uri}")
    print(f"ocds={result.ocds_report.get('ocds_n')} matched={result.ocds_report.get('matched_n')}")
    print(f"official_ocds={official['ocds_jsonl']}")
    print(f"official_rfb={official['rfb_index']}")
    print(f"orgao={orgao['cnpj']} contratacao={contratacao['pncpId']} items={len(items)}")
    print(f"flags={sorted(kinds)}")
    return 0


def _check_defs() -> None:
    from compras_ingest.assets import assert_asset_graph

    try:
        assert_asset_graph()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


def _assert_official_urls(settings: Settings) -> dict:
    try:
        ocds = resolve_ocds_feed(settings.ocds_year)
        rfb = resolve_receita_index()
    except Exception as exc:
        raise SystemExit(f"official URL resolve failed: {exc}") from exc
    if ocds.registry_url != OCDS_OCP_REGISTRY_URL:
        raise SystemExit(f"OCDS registry URL is not OCP publication 157: {ocds.registry_url}")
    if "data.open-contracting.org" not in ocds.jsonl_url:
        raise SystemExit(f"OCDS download host is not data.open-contracting.org: {ocds.jsonl_url}")
    if "/publication/157/" not in ocds.jsonl_url or not ocds.jsonl_url.endswith(".jsonl.gz"):
        raise SystemExit(f"OCDS download is not the publication 157 jsonl: {ocds.jsonl_url}")
    if f"name={settings.ocds_year}.jsonl.gz" not in ocds.jsonl_url and "name=full.jsonl.gz" not in ocds.jsonl_url:
        raise SystemExit(f"OCDS download is not a year or full jsonl from the OCP page: {ocds.jsonl_url}")
    if rfb.index_url != RFB_SHARE_URL:
        raise SystemExit(f"Receita index URL is not official: {rfb.index_url}")
    if "arquivos.receitafederal.gov.br" not in rfb.webdav_root:
        raise SystemExit(f"Receita WebDAV host is not official: {rfb.webdav_root}")
    if not rfb.month or not rfb.files:
        raise SystemExit("Receita index resolved without month or files")
    return {"ocds_jsonl": ocds.jsonl_url, "rfb_index": rfb.index_url, "rfb_month": rfb.month}


def _assert_landing(settings: Settings, sha256: str) -> None:
    store = LandingStore(settings)
    keys = store.list_parquet("compras_gov")
    if not keys:
        raise SystemExit("no compras_gov parquet in landing")
    hashed = [k for k in keys if sha256 in k and k.endswith(".parquet")]
    if not hashed:
        raise SystemExit(f"hashed parquet {sha256} missing")
    if "/date=" not in hashed[0] and "date=" not in hashed[0]:
        raise SystemExit(f"landing not partitioned by date: {hashed[0]}")
    if len(sha256) != 64:
        raise SystemExit("content hash is not sha256")


def _assert_tier_a_landing(settings: Settings, ocds_report: dict) -> None:
    store = LandingStore(settings)
    for source in ("ocds", "receita_cnpj", "receita_cnpj_socios"):
        keys = [k for k in store.list_parquet(source) if k.endswith(".parquet")]
        if not keys:
            raise SystemExit(f"no {source} parquet in landing")
        for key in keys:
            if "date=" not in key:
                raise SystemExit(f"{source} not partitioned by date: {key}")
            digest = Path(key).stem
            if len(digest) != 64:
                raise SystemExit(f"{source} key is not content-hashed sha256: {key}")
            df = store.read_parquet(key)
            blobs = [str(v) for col in df.columns for v in df[col].to_list()]
            assert_no_raw_cpf(blobs)
            if source == "receita_cnpj" and df.is_empty():
                raise SystemExit("receita_cnpj landed empty from fixture")
            if source == "receita_cnpj_socios":
                if df.is_empty():
                    raise SystemExit("receita_cnpj_socios landed empty from fixture")
                if mask_cpf(RAW_CPF) not in " ".join(blobs):
                    raise SystemExit("receita socios missing masked CPF")
            if source == "ocds" and df.is_empty():
                raise SystemExit("ocds landed empty from fixture")
    if ocds_report.get("skipped"):
        raise SystemExit("ocds_crosscheck skipped")
    if ocds_report.get("primary") is not False:
        raise SystemExit("OCDS must stay secondary")
    if int(ocds_report.get("ocds_n") or 0) < 1:
        raise SystemExit("OCDS fixture produced no releases")
    if int(ocds_report.get("matched_n") or 0) < 1:
        raise SystemExit("OCDS cross-check matched no compras ids")


def _assert_write_once(settings: Settings) -> None:
    store = LandingStore(settings)
    first = store.list_parquet("ocds")
    ref, _ = land_ocds(settings, store=store)
    if ref.key not in first:
        raise SystemExit("ocds reland produced a new content-hashed key")
    if len(store.list_parquet("ocds")) != len(first):
        raise SystemExit("ocds reland wrote a second parquet")
    basicos: set[str] = set()
    for key in store.list_parquet("compras_gov"):
        basicos |= cnpj_basicos_from_frame(store.read_parquet(key))
    receita_first = store.list_parquet("receita_cnpj")
    socios_first = store.list_parquet("receita_cnpj_socios")
    land_receita_cnpj(settings, store, cnpj_basicos=basicos)
    if len(store.list_parquet("receita_cnpj")) != len(receita_first):
        raise SystemExit("receita reland wrote a second parquet")
    if len(store.list_parquet("receita_cnpj_socios")) != len(socios_first):
        raise SystemExit("receita socios reland wrote a second parquet")


if __name__ == "__main__":
    sys.exit(main())
