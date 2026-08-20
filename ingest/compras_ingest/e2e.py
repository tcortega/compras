from __future__ import annotations

import sys

from compras_detect.tier1 import run_tier1
from compras_ingest.cpf import assert_no_raw_cpf, mask_cpf
from compras_ingest.landing import LandingStore
from compras_ingest.pipeline import _collect_landing_records, land_second_snapshot, run_compras_slice
from compras_ingest.settings import Settings
from compras_ingest.warehouse import fetch_contratacao, fetch_items_for, fetch_one_orgao, fetch_raw_text_blobs, write_flags


ORGAO_CNPJ = "29477000000180"
PNCP_ID = "29477000000180-1-2024-000001"
RAW_CPF = "12345678901"


def main() -> int:
    settings = Settings.from_env()
    _check_defs()
    result = run_compras_slice(settings)
    _assert_landing(settings, result.landing.sha256)
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
    for key in store.list_parquet("compras_gov"):
        df = store.read_parquet(key)
        blobs.extend(str(v) for col in df.columns for v in df[col].to_list())
    assert_no_raw_cpf(blobs)
    if mask_cpf(RAW_CPF) not in " ".join(blobs):
        raise SystemExit("masked CPF not present in landing")
    print("e2e ok")
    print(f"landing={result.landing.uri}")
    print(f"orgao={orgao['cnpj']} contratacao={contratacao['pncpId']} items={len(items)}")
    print(f"flags={sorted(kinds)}")
    return 0


def _check_defs() -> None:
    from compras_ingest.definitions import defs

    keys = [k.to_user_string() for k in defs.get_repository_def().asset_graph.get_all_asset_keys()]
    expected = {
        "catalogo_cnbs",
        "receita_cnpj",
        "compras_gov",
        "ocds_crosscheck",
        "warehouse_entities",
        "tier1_flags",
    }
    missing = expected - set(keys)
    if missing:
        raise SystemExit(f"dagster defs missing {missing}")


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


if __name__ == "__main__":
    sys.exit(main())
