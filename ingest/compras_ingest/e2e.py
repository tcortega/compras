from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from dataclasses import replace
from datetime import date
from pathlib import Path

import httpx

from compras_detect.adjacency import load_expected as load_adjacency_expected
from compras_detect.cobid import (
    KIND_COVER,
    KIND_ROTATION,
    KIND_SKEW,
    KIND_VARIANCE,
    load_expected as load_cobid_expected,
    load_thresholds as load_cade_thresholds,
)
from compras_detect.data_error import anomaly_pool, detect_data_errors
from compras_detect.tier1 import run_tier1
from compras_detect.tier1.cnae_mismatch import (
    ALLOW_PATH as CNAE_ALLOW_PATH,
    KIND as CNAE_KIND,
    OFFICIAL_HOSTS as CNAE_OFFICIAL_HOSTS,
    load_allowlist,
)
from compras_detect.tier1.fracionamento import (
    KIND_CLUSTER as FRAC_CLUSTER_KIND,
    KIND_OVER as FRAC_OVER_KIND,
    THRESH_PATH,
    load_thresholds,
)
from compras_ingest.cpf import assert_no_raw_cpf, is_cnpj, mask_cpf
from compras_ingest.landing import LandingStore
from compras_ingest.ids import sha256_bytes
from compras_ingest.official import (
    CGU_CEIS_LISTING_URL,
    CGU_CNEP_LISTING_URL,
    CGU_HOSTS,
    COMPRAS_GOV_HOSTS,
    COMPRAS_GOV_INDEX,
    OCDS_OCP_REGISTRY_URL,
    OFFICIAL_HOSTS,
    PNCP_API_BASE,
    PNCP_COMPRA_PATH,
    PNCP_CONSULTA_BASE,
    PNCP_CONSULTA_OPENAPI,
    PNCP_CONSULTA_SWAGGER,
    PNCP_ITEM_RESULTADOS_PATH,
    PNCP_ITENS_PATH,
    PNCP_PUBLICACAO_PATH,
    RFB_SHARE_URL,
    TCE_RS_EXAMPLE_URL,
    TCE_RS_HOSTS,
    TCE_RS_LEIAUTE_URL,
    TCE_SP_HOSTS,
    TCE_SP_LISTING_URL,
    PncpOfficial,
    assert_cgu_zip_url,
    assert_official_host,
    ckan_zip_from_package,
    deny_resolve,
    fixture_cgu_ceis_cnep_official,
    fixture_compras_gov_diario_official,
    fixture_compras_gov_mensal_official,
    fixture_compras_gov_official,
    fixture_ocds_official,
    fixture_pncp_official,
    fixture_receita_official,
    fixture_tce_rs_official,
    fixture_tce_sp_official,
    licitacao_zip_from_listing,
    tce_rs_ckan_url,
    tce_rs_portal_url,
)
from compras_ingest.pipeline import (
    _collect_landing_records,
    land_second_snapshot,
    run_compras_slice,
    warehouse_data_error_fixture,
)
from compras_ingest.pncp_ids import complete_compra_keys, live_ibge_targets
from compras_ingest.slice import SLICE_IBGE_CODES
from compras_ingest.settings import Settings
from compras_ingest.sources.catalogo_cnbs import land_catalogo_cnbs
from compras_ingest.sources.compras_gov import land_compras_gov
from compras_ingest.sources.ocds import land_ocds
from compras_ingest.sources.pncp_consulta import (
    CURSOR_KEY,
    GAPS_CURSOR_KEY,
    MIN_INTERVAL_S,
    FixtureTransport,
    InterruptTransport,
    RateLimiter,
    land_pncp_consulta,
    land_pncp_consulta_gaps,
)
from compras_ingest.sources.cgu_ceis_cnep import SOURCE as CGU_SOURCE
from compras_ingest.sources.cgu_ceis_cnep import land_cgu_ceis_cnep, load_landed_sanctions
from compras_ingest.sources.receita_cnpj import cnpj_basicos_from_frame, land_receita_cnpj
from compras_ingest.sources.tce_rs_licitacon import SOURCE as TCE_RS_SOURCE
from compras_ingest.sources.tce_rs_licitacon import TABLE_COL as TCE_RS_TABLE
from compras_ingest.sources.tce_rs_licitacon import land_tce_rs_licitacon
from compras_ingest.sources.tce_sp_licitacao import SOURCE as TCE_SP_SOURCE
from compras_ingest.sources.tce_sp_licitacao import land_tce_sp_licitacao
from compras_ingest.ids import item_id
from compras_ingest.warehouse import (
    fact_columns,
    fetch_adjacencies,
    fetch_all_items,
    fetch_catalog_codes,
    fetch_cnaes,
    fetch_contratacao,
    fetch_contratacao_anos,
    fetch_exclusions,
    fetch_flags,
    fetch_fornecedor_socios,
    fetch_item_facts,
    fetch_items_for,
    fetch_landing_sources,
    fetch_cobid_edges,
    fetch_cobid_screens,
    fetch_explorer_text_blobs,
    fetch_one_orgao,
    fetch_participants,
    fetch_raw_text_blobs,
    item_columns,
    write_entities,
    write_facts,
    write_flags,
    fetch_counts,
    fetch_fact_count,
    fetch_record_hashes,
)
from compras_ingest.ids import item_id
from decimal import Decimal

from compras_normalize.catalog import load_catalog_from_dir
from compras_normalize.classifier import QUALITY_EXACT, QUALITY_KNN, QUALITY_NONE, description_hash
from compras_normalize.items import normalize_frame
from compras_normalize.text import fold, parse_decimal
from compras_normalize.units import load_unit_table
from compras_ingest.csvio import read_csv


ORGAO_CNPJ = "29477000000180"
PNCP_ID = "29477000000180-1-2024-000001"
FETCH_ANUAL_2024 = "C-FETCH-2024"
FETCH_ANUAL_2025 = "C-FETCH-2025"
FETCH_ANUAL_2026 = "C-FETCH-2026"
RAW_CPF = "12345678901"
LANDED_SOURCES = (
    "compras_gov",
    "ocds",
    "receita_cnpj",
    "receita_cnpj_socios",
    "receita_cnpj_cnaes",
    "receita_cnpj_qualificacoes",
    "pncp_consulta",
    TCE_SP_SOURCE,
    TCE_RS_SOURCE,
    CGU_SOURCE,
)
TCE_WINNER_CNPJ = "34.914.897/0001-80"
TCE_LOSER_CNPJ = "11.021.249/0001-08"
TCE_OTHER_CNPJ = "00.000.000/0001-91"
TCE_LOSER_PROPOSTA = "32250,0"
TCE_RS_WINNER_CNPJ = "03722885000120"
TCE_RS_LOSER_CNPJ = "91549055000100"
TCE_RS_LOSER_PROPOSTA = "5493164,86"
SANCTION_CNPJ_A = "44555666000172"
SANCTION_CNPJ_CNEP = "11222333000181"
SANCTION_CNPJ_B = "01328535000159"
SANCTION_CNPJ_C = "47140401000100"
SANCTION_CNPJ_D = "00802002000102"
SANCTION_CNPJ_E = "01042740000153"
SANCTION_OVERLAP = frozenset({SANCTION_CNPJ_A, SANCTION_CNPJ_CNEP})
SANCTION_CLEAN = frozenset({SANCTION_CNPJ_B, SANCTION_CNPJ_C, SANCTION_CNPJ_D, SANCTION_CNPJ_E})
AGE_FLAG_KIND = "cnpj_age"
AGE_INFO_KIND = "cnpj_age_info"
AGE_YOUNG_CNPJ = "11222333000181"
AGE_INFO_CNPJ = "55666777000193"
AGE_OLD_CNPJ = "44555666000172"
AGE_FUTURE_CNPJ = "66777888000104"
AGE_NOOPEN_CNPJ = "77888999000115"
AGE_NODATE_CNPJ = "88999000000126"
AGE_YOUNG_IDS = frozenset(
    {
        "I-2024-000001",
        "I-2024-000007",
        "I-2024-000008",
        "I-2024-000009",
        "I-2024-000010",
        "I-2024-000011",
    }
)
AGE_INFO_IDS = frozenset({"I-2024-B2-INFO"})
AGE_SILENT_IDS = frozenset(
    {
        "I-2024-000002",
        "I-2024-000004",
        "I-2024-000005",
        "I-2024-000006",
        "I-2024-B2-FUTURE",
        "I-2024-B2-NOOPEN",
        "I-2024-B2-NOAWARD",
        "I-2024-B4-PRICE",
        "I-2024-B4-QTY",
        "I-2024-B4-SUPPLIER",
        "I-2024-B4-DESC",
        "I-2024-B4-SAME",
        "I-2024-B4-PREPUB",
    }
)
FRAC_OVER_IDS = frozenset({"I-2024-B3-OVER-1", "I-2024-B3-OVER-2", "I-2024-B3-OVER-3"})
FRAC_CLUSTER_IDS = frozenset({"I-2024-B3-CLUSTER-1", "I-2024-B3-CLUSTER-2", "I-2024-B3-CLUSTER-3"})
FRAC_SILENT_IDS = frozenset(
    {
        "I-2024-000004",
        "I-2024-000005",
        "I-2024-000006",
        "I-2024-B3-BIG-1",
        "I-2024-B3-BIG-2",
        "I-2024-B3-OTHERCLS",
        "I-2024-B3-PREGAO-1",
        "I-2024-B3-PREGAO-2",
        "I-2024-B3-PREGAO-3",
        "I-2025-B3-OTHERYR-1",
        "I-2025-B3-OTHERYR-2",
    }
)
FRAC_KINDS = frozenset({FRAC_OVER_KIND, FRAC_CLUSTER_KIND})
FRAC_OFFICIAL_HOSTS = ("planalto.gov.br", "in.gov.br", "compras.gov.br", "gov.br")
FRAC_DELTA_TOKENS = (
    "orgao=",
    "class_key=",
    "year=",
    "n=",
    "sum=",
    "threshold=",
    "decree=",
    "kind=",
    "rule=",
)
EDIT_KIND = "retroactive_edit"
EDIT_FLAG_IDS = frozenset({"I-2024-B4-PRICE", "I-2024-B4-QTY", "I-2024-B4-SUPPLIER"})
EDIT_ABSENT_IDS = frozenset({"I-2024-B4-DESC", "I-2024-B4-SAME", "I-2024-B4-PREPUB"})
CNAE_HIT_IDS = frozenset({"I-2024-B5-HIT-FOOD", "I-2024-B5-HIT-HOME", "I-2024-B5-HIT-OUT"})
CNAE_CLEAN_IDS = frozenset(
    {
        "I-2024-B5-CLEAN-PRI",
        "I-2024-B5-CLEAN-SEC",
        "I-2024-B5-CLEAN-UNMAP",
        "I-2024-B5-CLEAN-NOCNAE",
        "I-2024-B5-CLEAN-NOCAT",
        "I-2024-B5-CLEAN-SERV",
    }
)
CNAE_DELTA_TOKENS = ("class=", "cnae=", "secondary=", "allowed=", "table=")
CNAE_BANNED_DELTA = re.compile(r"fraude|corrupto|roubo|acus", re.I)
OFFICIAL_HOST_NEEDLES = (
    "compras.gov.br",
    "pncp.gov.br",
    "dados.gov.br",
    "planalto",
    "tce.sp.gov.br",
    "tce.rs.gov.br",
    "tcers.tc.br",
    "cgu.gov.br",
    "portaldatransparencia.gov.br",
    "receitafederal.gov.br",
    "open-contracting.org",
)
TCE_RS_TABLES = {
    "LICITANTE",
    "PROPOSTA",
    "LOTE_PROPOSTA",
    "ITEM_PROPOSTA",
    "LICITACAO",
    "LOTE",
    "ITEM",
}
A2_PNCP = "29477000000180-1-2024-00A201"
A2_PAPEL = "111111"
A2_CANETA = "333333"
A2_DIPIRONA = "222222"
A2_EXPECTED = {
    "a2-knn-papel": (A2_PAPEL, QUALITY_KNN),
    "a2-knn-papel-2": (A2_PAPEL, QUALITY_KNN),
    "a2-amb": ("", QUALITY_NONE),
    "a2-exact": (A2_CANETA, QUALITY_EXACT),
    "a2-spec-med": (A2_DIPIRONA, QUALITY_EXACT),
    "a2-spec-empty": ("", QUALITY_NONE),
    "a2-cx-com": (A2_PAPEL, QUALITY_EXACT),
    "a2-pct": (A2_PAPEL, QUALITY_EXACT),
    "a2-cx": (A2_PAPEL, QUALITY_EXACT),
    "a2-foobar": (A2_PAPEL, QUALITY_EXACT),
}
DATA_ERROR_SNAPSHOT = "data-error-golden"
DATA_ERROR_EXPECTED = {
    "de-mismatch": frozenset({"qty_unit_price_neq_total"}),
    "de-shift": frozenset({"decimal_shift"}),
    "de-collapse": frozenset({"qty_eq_1_collapse"}),
    "de-zero-qty": frozenset({"zero_or_negative"}),
    "de-neg-unit": frozenset({"zero_or_negative"}),
    "de-dup-b": frozenset({"duplicate_row"}),
    "de-dup-c": frozenset({"duplicate_row"}),
    "de-catalog": frozenset({"catalog_magnitude"}),
    "de-fracassado": frozenset({"excluded_no_award"}),
    "de-deserto": frozenset({"excluded_no_award"}),
    "de-anulado": frozenset({"excluded_no_award"}),
    "de-revogado": frozenset({"excluded_no_award"}),
    "de-cancelado": frozenset({"excluded_no_award"}),
    "de-204": frozenset({"excluded_no_award"}),
    "de-andamento": frozenset({"excluded_no_award"}),
}
DATA_ERROR_CLEAN = frozenset(
    {
        "de-clean",
        "de-peer-2",
        "de-peer-3",
        "de-peer-4",
        "de-nearmiss",
        "de-dup-a",
        "de-homologado",
        "de-nocat",
        "de-andamento-award",
    }
)
LIVE_NO_AWARD_IDS = (
    "9805950590008202400004",
    "9865890590120202400010",
)
MAIN_MISMATCH_RECORD = "I-2024-000002"
PNCP_COMPRA_1 = "29477000000180-1-000001/2024"
PNCP_COMPRA_2 = "29477000000180-1-000002/2024"
PNCP_COMPRA_GAP = "29477000000180-1-000099/2024"
PNCP_GAP_DESC = "GRAMPEADOR DE MESA METALICO"
EXTRA_ORGAOS = (
    ("28521748000159", "3303302", "RJ"),
    ("46137410000180", "3506003", "SP"),
    ("88830609000139", "4305108", "RS"),
    ("83169623000110", "4209102", "SC"),
    ("18431312000115", "3170206", "MG"),
    ("75771477000170", "4113700", "PR"),
    ("14043574000151", "2910800", "BA"),
    ("10091536000113", "2604106", "PE"),
    ("01067479000146", "5201108", "GO"),
    ("27165554000103", "3205200", "ES"),
    ("08993917000146", "2504009", "PB"),
    ("07616162000106", "2303709", "CE"),
    ("06158455000116", "2105302", "MA"),
    ("12198693000158", "2700300", "AL"),
    ("20267427000168", "5003702", "MS"),
    ("05853163000130", "1504208", "PA"),
    ("03507548000110", "5108402", "MT"),
    ("04092672000125", "1100122", "RO"),
    ("08170862000174", "2403251", "RN"),
    ("04012548000102", "1200203", "AC"),
    ("23066640000108", "1600600", "AP"),
    ("01613031000180", "1400472", "RR"),
    ("76282656000106", "4115200", "PR"),
    ("45176005000108", "3554102", "SP"),
    ("76208867000107", "4104808", "PR"),
    ("18338178000102", "3136702", "MG"),
    ("76206606000140", "4108304", "PR"),
    ("88488366000100", "4316907", "RS"),
    ("22678874000135", "3143302", "MG"),
    ("20622890000180", "3127701", "MG"),
    ("88577416000118", "4304606", "RS"),
    ("82777301000190", "4209300", "SC"),
    ("05182233000761", "1506807", "PA"),
    ("02056729000105", "5218805", "GO"),
    ("14217327000124", "2924009", "BA"),
    ("11251832000105", "2613701", "PE"),
    ("07587975000107", "2304202", "CE"),
    ("04104816000116", "1100023", "RO"),
    ("27165729000174", "3201506", "ES"),
    ("05121991000184", "1502400", "PA"),
    ("18291351000164", "3122306", "MG"),
    ("29138344000143", "3303906", "RJ"),
    ("19876424000142", "3131307", "MG"),
    ("29115474000160", "3302403", "RJ"),
    ("18715409000150", "3157807", "MG"),
    ("28606630000123", "3303401", "RJ"),
    ("44477909000100", "3529005", "SP"),
    ("83102285000107", "4202008", "SC"),
    ("46316600000164", "3523107", "SP"),
    ("46177531000155", "3541000", "SP"),
    ("76105543000135", "4125506", "PR"),
    ("46523056000121", "3552502", "SP"),
    ("44959021000104", "3518701", "SP"),
    ("46523049000120", "3513009", "SP"),
    ("22980999000115", "1505536", "PA"),
    ("46694139000183", "3524402", "SP"),
    ("28741080000155", "3301900", "RJ"),
    ("29131075000193", "3302700", "RJ"),
)


def main() -> int:
    os.environ["COMPRAS_E2E"] = "1"
    os.environ["CLASSIFIER_FIXTURE"] = "1"
    settings = Settings.from_env()
    _check_defs()
    _assert_fracionamento_table()
    _assert_cnae_allowlist()
    _assert_compras_gov_fetch_anual_year_columns(settings)
    with _official_hosts_blocked():
        official = _assert_official_urls(settings)
        _assert_compras_gov_official_urls(settings)
        _assert_pncp_spacing_and_resume(settings)
        _assert_pncp_gaps_job(settings)
        result = run_compras_slice(settings)
        _assert_landing(settings, result.landing.sha256)
        _assert_compras_gov_years(settings)
        _assert_tier_a_landing(settings, result.ocds_report)
        _assert_tce_sp_landing(settings)
        _assert_tce_rs_landing(settings)
        _assert_cgu_ceis_cnep_landing(settings)
        _assert_write_once(settings)
        _assert_refetch_schedule(settings)
        _assert_incremental_schedules(settings)
        _assert_nightly_detector_schedule(settings)
        _assert_land_idempotency(settings)
        _assert_data_error_suite(settings, result.items)
        _assert_a2(settings)
        _assert_a3_labels()
        _assert_f3_dossier()
    _assert_tce_sp_not_public(settings)
    _assert_tce_rs_not_public(settings)
    _assert_coverage_warehouse(settings)
    orgao = fetch_one_orgao(settings, ORGAO_CNPJ)
    if orgao is None:
        raise SystemExit(f"missing orgao {ORGAO_CNPJ}")
    for cnpj, ibge, uf in EXTRA_ORGAOS:
        extra = fetch_one_orgao(settings, cnpj)
        if extra is None:
            raise SystemExit(f"missing extra orgao {cnpj}")
        if str(extra.get("municipioIbge") or "") != ibge:
            raise SystemExit(f"{cnpj}: expected IBGE {ibge}, got {extra.get('municipioIbge')}")
        if str(extra.get("uf") or "") != uf:
            raise SystemExit(f"{cnpj}: expected UF {uf}, got {extra.get('uf')}")
    contratacao = fetch_contratacao(settings, PNCP_ID)
    if contratacao is None:
        raise SystemExit(f"missing contratacao {PNCP_ID}")
    items = fetch_items_for(settings, str(contratacao["id"]))
    if not items:
        raise SystemExit("missing item rows for contratacao")
    _assert_pncp_gap_warehouse(settings)
    _assert_units(settings, result.items)
    store = LandingStore(settings)
    mutate = str(result.items["record_id"][0])
    hashes_before_edit = {Path(k).stem for k in store.list_parquet("compras_gov")}
    land_second_snapshot(settings, mutate, store)
    landing_records = _collect_landing_records(store, "compras_gov")
    sanctions = load_landed_sanctions(store)
    if sanctions is None or sanctions.is_empty():
        raise SystemExit("landed sanctions missing when run_tier1 should load them")
    flags = run_tier1(result.items, landing_records=landing_records, sanctions=sanctions)
    write_flags(settings, flags, result.items)
    stored = fetch_flags(settings, state="detected")
    kinds = {str(row["kind"]) for row in stored}
    _assert_sanction_flags(result.items, result.flags, stored)
    _assert_cnpj_age_flags(result.items, result.flags, stored)
    _assert_fracionamento_flags(result.items, flags, stored)
    _assert_cnae_mismatch_flags(result.items, flags, stored)
    _assert_retroactive_edit_flags(result.items, flags, stored, hashes_before_edit, store)
    _assert_receita_adjacency(settings)
    _assert_fornecedor_receita_facts(settings)
    _assert_cobid_suite(settings)
    if "qty_unit_price_neq_total" not in kinds:
        raise SystemExit("warehouse missing qty_unit_price_neq_total after write_flags")
    if "retroactive_edit" not in kinds:
        raise SystemExit("warehouse missing retroactive_edit after second landing")
    if AGE_FLAG_KIND not in kinds:
        raise SystemExit("warehouse missing cnpj_age after write_flags")
    if AGE_INFO_KIND not in kinds:
        raise SystemExit("warehouse missing cnpj_age_info after write_flags")
    if FRAC_OVER_KIND not in kinds:
        raise SystemExit("warehouse missing fracionamento after write_flags")
    if FRAC_CLUSTER_KIND not in kinds:
        raise SystemExit("warehouse missing fracionamento_cluster after write_flags")
    if CNAE_KIND not in kinds:
        raise SystemExit("warehouse missing cnae_mismatch after write_flags")
    for row in stored:
        if not row.get("itemId"):
            raise SystemExit("warehouse flag missing itemId")
        if not row.get("delta"):
            raise SystemExit("warehouse flag missing delta")
        if not row.get("snapshotId"):
            raise SystemExit("warehouse flag missing snapshotId")
        if str(row.get("methodologyVersion") or "") != settings.methodology_version:
            raise SystemExit(
                f"warehouse flag methodologyVersion {row.get('methodologyVersion')!r} "
                f"!= {settings.methodology_version!r}"
            )
        if str(row.get("state") or "") != "detected":
            raise SystemExit(f"warehouse flag state is not detected: {row.get('state')}")
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
    print(f"official_pncp={official['pncp_consulta']}")
    print(f"official_tce_sp={official['tce_sp_zip']}")
    print(f"official_tce_rs={official['tce_rs_zip']}")
    print(f"official_cgu_ceis={official['cgu_ceis_zip']}")
    print(f"official_cgu_cnep={official['cgu_cnep_zip']}")
    print(f"orgao={orgao['cnpj']} contratacao={contratacao['pncpId']} items={len(items)}")
    print(f"flags={sorted(kinds)}")
    print(f"exclusions={result.exclusion_rows}")
    print(f"adjacencies={result.adjacency_rows}")
    print(f"participants={result.participant_rows}")
    print(f"cobid_edges={result.cobid_edge_rows}")
    print(f"cobid_screens={result.cobid_screen_rows}")
    return 0


def _reasons_by_record(exclusions) -> dict[str, set[str]]:
    got: dict[str, set[str]] = {}
    for row in exclusions.iter_rows(named=True):
        rid = str(row.get("record_id") or "")
        got.setdefault(rid, set()).add(str(row["reason"]))
    return got


def _assert_data_error_suite(settings: Settings, main_items) -> None:
    items, exclusions, pool = warehouse_data_error_fixture(settings)
    got = _reasons_by_record(exclusions)
    expected_ids = set(DATA_ERROR_EXPECTED) | DATA_ERROR_CLEAN
    have_ids = {str(v) for v in items["record_id"].to_list()}
    if have_ids != expected_ids:
        raise SystemExit(f"data-error fixture record_ids drifted: {sorted(have_ids)}")
    extra = {rid: reasons for rid, reasons in got.items() if rid not in DATA_ERROR_EXPECTED}
    missing = {
        rid: DATA_ERROR_EXPECTED[rid]
        for rid in DATA_ERROR_EXPECTED
        if got.get(rid) != DATA_ERROR_EXPECTED[rid]
    }
    if extra or missing:
        raise SystemExit(f"data-error tags mismatch extra={extra} missing={missing} got={got}")
    for rid in DATA_ERROR_CLEAN:
        if rid in got:
            raise SystemExit(f"clean data-error row was tagged: {rid} {got[rid]}")
    if "de-clean" in got:
        raise SystemExit("clean row present in exclusions")

    pool_ids = {str(v) for v in pool["record_id"].to_list()}
    for rid in DATA_ERROR_EXPECTED:
        if rid in pool_ids:
            raise SystemExit(f"excluded {rid} still in anomaly_pool")
    for rid in DATA_ERROR_CLEAN:
        if rid not in pool_ids:
            raise SystemExit(f"clean {rid} missing from anomaly_pool")
    live_pool = anomaly_pool(items, exclusions)
    if set(live_pool["record_id"].to_list()) != pool_ids:
        raise SystemExit("anomaly_pool() drifted from warehouse fixture pool")

    stored_items = fetch_all_items(settings)
    stored_ids = {str(row["id"]) for row in stored_items}
    for row in items.iter_rows(named=True):
        iid = item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or ""))
        if iid not in stored_ids:
            raise SystemExit(f"data-error item missing from postgres item: {row.get('record_id')}")

    id_to_rid = {
        item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or "")): str(row.get("record_id") or "")
        for row in items.iter_rows(named=True)
    }
    stored = fetch_exclusions(settings, snapshot_id=DATA_ERROR_SNAPSHOT)
    stored_got: dict[str, set[str]] = {}
    for row in stored:
        rid = id_to_rid.get(str(row["itemId"]))
        if not rid:
            raise SystemExit(f"item_exclusion itemId not in golden fixture: {row['itemId']}")
        stored_got.setdefault(rid, set()).add(str(row["reason"]))
    if stored_got != {k: set(v) for k, v in DATA_ERROR_EXPECTED.items()}:
        raise SystemExit(f"postgres item_exclusion tags mismatch got={stored_got}")

    main_exclusions = detect_data_errors(main_items)
    main_got = _reasons_by_record(main_exclusions)
    if "qty_unit_price_neq_total" not in main_got.get(MAIN_MISMATCH_RECORD, set()):
        raise SystemExit("warehouse slice missed qty_unit_price_neq_total exclusion")
    main_pool_ids = {str(v) for v in anomaly_pool(main_items, main_exclusions)["record_id"].to_list()}
    for rid in LIVE_NO_AWARD_IDS:
        if "excluded_no_award" not in main_got.get(rid, set()):
            raise SystemExit(f"live no-resultado row missed excluded_no_award: {rid}")
        if rid in main_pool_ids:
            raise SystemExit(f"live no-resultado row stayed in anomaly_pool: {rid}")
    homo = None
    for row in items.iter_rows(named=True):
        if str(row.get("record_id") or "") == "de-homologado":
            homo = row
            break
    if homo is None:
        raise SystemExit("planted de-homologado missing from golden fixture")
    if str(homo.get("valor_unitario_estimado") or "") != "5000.00":
        raise SystemExit("de-homologado CSV estimate plant drifted")
    if str(homo.get("valor_unitario_resultado") or "") != "5.00":
        raise SystemExit("de-homologado resultado plant drifted")
    if "de-homologado" in got:
        raise SystemExit("de-homologado was scored from the CSV estimate")
    main_mismatch = None
    for row in main_items.iter_rows(named=True):
        if str(row.get("record_id") or "") == MAIN_MISMATCH_RECORD:
            main_mismatch = row
            break
    if main_mismatch is None:
        raise SystemExit(f"main slice missing {MAIN_MISMATCH_RECORD}")
    main_iid = item_id(str(main_mismatch.get("pncp_id") or ""), MAIN_MISMATCH_RECORD)
    main_stored = fetch_exclusions(settings, item_id=main_iid, reason="qty_unit_price_neq_total")
    if not main_stored:
        raise SystemExit("warehouse write path did not persist qty_unit_price_neq_total exclusion")
    if main_iid not in stored_ids:
        raise SystemExit("excluded main-slice item missing from postgres item")
    live_no_award = None
    for row in main_items.iter_rows(named=True):
        if str(row.get("record_id") or "") == LIVE_NO_AWARD_IDS[0]:
            live_no_award = row
            break
    if live_no_award is None:
        raise SystemExit(f"main slice missing live no-award {LIVE_NO_AWARD_IDS[0]}")
    live_iid = item_id(str(live_no_award.get("pncp_id") or ""), LIVE_NO_AWARD_IDS[0])
    live_stored = fetch_exclusions(settings, item_id=live_iid, reason="excluded_no_award")
    if not live_stored:
        raise SystemExit("warehouse write path did not persist excluded_no_award")
    if live_iid not in stored_ids:
        raise SystemExit("excluded_no_award item missing from postgres item")


def _a2_dir() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        cand = p / "normalize" / "fixtures" / "a2"
        if cand.exists():
            return cand
    raise SystemExit("normalize/fixtures/a2 missing")


def _assert_a2(settings: Settings) -> None:
    os.environ["CLASSIFIER_FIXTURE"] = "1"
    if os.environ.get("CLASSIFIER_LLM", "").strip():
        raise SystemExit("e2e must not enable CLASSIFIER_LLM")
    root = _a2_dir()
    catalog = load_catalog_from_dir(root / "catalog")
    units = load_unit_table()
    raw = read_csv(root / "items.csv")
    first = normalize_frame(raw, catalog, units, None, "a2-golden", settings.methodology_version)
    if first.height != len(A2_EXPECTED):
        raise SystemExit(f"a2 fixture row count drifted: {first.height}")
    got = {}
    knn_only = []
    by_hash: dict[str, set[str]] = {}
    for row in first.iter_rows(named=True):
        rid = str(row.get("record_id") or "")
        got[rid] = (str(row.get("catmat") or ""), str(row.get("catmat_match_quality") or ""))
        if got[rid][1] == QUALITY_KNN:
            knn_only.append(rid)
        desc_key = fold(str(row.get("descricao") or ""))
        by_hash.setdefault(description_hash(desc_key), set()).add(desc_key)
    if got != {k: (code, q) for k, (code, q) in A2_EXPECTED.items()}:
        raise SystemExit(f"a2 assignments mismatch got={got} expected={A2_EXPECTED}")
    if set(knn_only) != {"a2-knn-papel", "a2-knn-papel-2"}:
        raise SystemExit(f"a2 knn assignments were not the planted pair: {knn_only}")
    for digest, descs in by_hash.items():
        if len(descs) != 1:
            raise SystemExit(f"a2 description hash collision: {digest} {descs}")
    embeds_first = catalog.cache.embeds
    hits_first = catalog.cache.hits
    if embeds_first != 3:
        raise SystemExit(f"a2 embed count {embeds_first} != 3 distinct uncoded descriptions")
    if hits_first < 1:
        raise SystemExit("a2 duplicate description re-embedded instead of cache lookup")
    second = normalize_frame(raw, catalog, units, None, "a2-golden", settings.methodology_version)
    if catalog.cache.embeds != embeds_first:
        raise SystemExit("a2 second normalize re-embedded instead of cache lookup")
    if catalog.cache.hits <= hits_first:
        raise SystemExit("a2 second normalize did not hit the description-hash cache")
    by_rid = {str(r["record_id"]): r for r in first.iter_rows(named=True)}
    papel_hash = description_hash(fold(str(by_rid["a2-knn-papel"].get("descricao") or "")))
    papel_hash_2 = description_hash(fold(str(by_rid["a2-knn-papel-2"].get("descricao") or "")))
    if papel_hash != papel_hash_2:
        raise SystemExit("a2 duplicate descriptions did not share a hash")
    med = by_rid["a2-spec-med"]
    if str(med.get("spec_concentracao") or "") != "500mg/ml":
        raise SystemExit(f"a2 spec concentracao drifted: {med.get('spec_concentracao')}")
    if str(med.get("spec_tamanho") or "") != "20ml":
        raise SystemExit(f"a2 spec tamanho drifted: {med.get('spec_tamanho')}")
    if str(med.get("spec_dosagem") or "") != "":
        raise SystemExit(f"a2 spec invented dosagem: {med.get('spec_dosagem')}")
    empty = by_rid["a2-spec-empty"]
    if any(str(empty.get(c) or "") for c in ("spec_concentracao", "spec_dosagem", "spec_tamanho")):
        raise SystemExit(f"a2 empty spec invented tokens: {empty}")
    exact = by_rid["a2-exact"]
    if str(exact.get("catmat") or "") != A2_CANETA or str(exact.get("catmat_match_quality") or "") != QUALITY_EXACT:
        raise SystemExit("a2 official code was overwritten by classifier")
    caixa = by_rid["a2-cx-com"]
    if str(caixa.get("unidade_canonica") or "") != "un":
        raise SystemExit(f"CAIXA COM 10 canonical is not un: {caixa.get('unidade_canonica')}")
    if parse_decimal(caixa.get("valor_por_unidade_canonica")) != parse_decimal(caixa.get("valor_unitario")) / 10:
        raise SystemExit("CAIXA COM 10 factor is not 10")
    pacote = by_rid["a2-pct"]
    if parse_decimal(pacote.get("valor_por_unidade_canonica")) != parse_decimal(pacote.get("valor_unitario")) / 100:
        raise SystemExit("PACOTE C/ 100 factor is not 100")
    cx = by_rid["a2-cx"]
    if str(cx.get("unidade_canonica") or "") != "cx":
        raise SystemExit(f"CX without count left canonical {cx.get('unidade_canonica')}")
    if parse_decimal(cx.get("valor_por_unidade_canonica")) != parse_decimal(cx.get("valor_unitario")):
        raise SystemExit("CX without count invented a multiplier")
    foobar = by_rid["a2-foobar"]
    if str(foobar.get("unidade_canonica") or "") != "unknown":
        raise SystemExit(f"FOOBAR invented unit {foobar.get('unidade_canonica')}")
    if foobar.get("valor_por_unidade_canonica") not in (None, ""):
        raise SystemExit("FOOBAR invented a canonical price")
    write_entities(settings, first)
    write_facts(settings, first)
    cols = item_columns(settings)
    for col in ("specConcentracao", "specDosagem", "specTamanho"):
        if col not in cols:
            raise SystemExit(f"postgres item missing {col}")
    ch_cols = fact_columns(settings)
    for col in ("spec_concentracao", "spec_dosagem", "spec_tamanho"):
        if col not in ch_cols:
            raise SystemExit(f"clickhouse item_fact missing {col}")
    contratacao = fetch_contratacao(settings, A2_PNCP)
    if contratacao is None:
        raise SystemExit(f"missing a2 contratacao {A2_PNCP}")
    stored = fetch_items_for(settings, str(contratacao["id"]))
    by_desc = {str(row.get("descricao") or ""): row for row in stored}
    med_pg = by_desc.get("DIPIRONA SODICA 500MG/ML SOL INJ 20ML")
    if med_pg is None:
        raise SystemExit("a2 spec row missing from postgres item")
    if str(med_pg.get("specConcentracao") or "") != "500mg/ml":
        raise SystemExit(f"postgres specConcentracao drifted: {med_pg.get('specConcentracao')}")
    if str(med_pg.get("specTamanho") or "") != "20ml":
        raise SystemExit(f"postgres specTamanho drifted: {med_pg.get('specTamanho')}")
    if str(med_pg.get("catmat") or "") != A2_DIPIRONA:
        raise SystemExit("a2 spec official catmat was overwritten in warehouse")
    empty_pg = [row for row in stored if str(row.get("descricao") or "") == "SERVICO AVULSO EVENTUAL"]
    if not empty_pg:
        raise SystemExit("a2 empty spec row missing from postgres item")
    if any(empty_pg[0].get(c) not in (None, "") for c in ("specConcentracao", "specDosagem", "specTamanho")):
        raise SystemExit("postgres invented spec tokens on a numberless description")
    facts = fetch_item_facts(settings)
    med_facts = [row for row in facts if str(row.get("spec_concentracao") or "") == "500mg/ml"]
    if not med_facts:
        raise SystemExit("clickhouse item_fact missing planted spec_concentracao")
    if str(med_facts[0].get("spec_tamanho") or "") != "20ml":
        raise SystemExit(f"clickhouse spec_tamanho drifted: {med_facts[0].get('spec_tamanho')}")
    # second frame must match first assignments exactly
    second_got = {
        str(row.get("record_id") or ""): (str(row.get("catmat") or ""), str(row.get("catmat_match_quality") or ""))
        for row in second.iter_rows(named=True)
    }
    if second_got != got:
        raise SystemExit(f"a2 second pass drifted assignments: {second_got}")


def _assert_a3_labels() -> None:
    root = Path(__file__).resolve().parents[2]
    labels = root / "labels"
    if not (labels / "a3_sample.py").is_file():
        return
    if str(labels) not in sys.path:
        sys.path.insert(0, str(labels))
    import a3_sample

    a3_sample.e2e_check(root)


def _assert_f3_dossier() -> None:
    root = Path(__file__).resolve().parents[2]
    labels = root / "labels"
    if not (labels / "f3_dossier.py").is_file():
        return
    if str(labels) not in sys.path:
        sys.path.insert(0, str(labels))
    import f3_dossier

    f3_dossier.e2e_check(root)


def _assert_units(settings, normalized) -> None:
    if "unidade_canonica" not in normalized.columns:
        raise SystemExit("normalize missing unidade_canonica")
    price_col = (
        "valor_por_unidade_canonica"
        if "valor_por_unidade_canonica" in normalized.columns
        else "valor_unitario_base"
    )
    if price_col not in normalized.columns:
        raise SystemExit("normalize missing valor_por_unidade_canonica")
    if all(v in (None, "") for v in normalized["unidade_canonica"].to_list()):
        raise SystemExit("normalize unidade_canonica always null")
    if all(v in (None, "") for v in normalized[price_col].to_list()):
        raise SystemExit("normalize valor_por_unidade_canonica always null")

    cols = item_columns(settings)
    if "unidadeCanonica" not in cols:
        raise SystemExit("postgres item missing unidadeCanonica")
    if "valorPorUnidadeCanonica" not in cols:
        raise SystemExit("postgres item missing valorPorUnidadeCanonica")
    stored = fetch_all_items(settings)
    if not stored:
        raise SystemExit("postgres item is empty")
    if all(row.get("unidadeCanonica") in (None, "") for row in stored):
        raise SystemExit("postgres unidadeCanonica always null")
    if all(row.get("valorPorUnidadeCanonica") is None for row in stored):
        raise SystemExit("postgres valorPorUnidadeCanonica always null")

    by_unit = {}
    for row in stored:
        by_unit.setdefault(fold(row.get("unidadeMedida")), []).append(row)

    cx = by_unit.get("cx") or []
    if not cx:
        raise SystemExit("fixture missing CX item")
    if str(cx[0].get("unidadeCanonica") or "") != "cx":
        raise SystemExit(f"CX canonical is not cx: {cx[0].get('unidadeCanonica')}")
    cx_price = parse_decimal(cx[0].get("valorPorUnidadeCanonica"))
    cx_unit = parse_decimal(cx[0].get("valorUnitario"))
    if cx_price is None or cx_unit is None or abs(cx_price - cx_unit) > Decimal("0.000001"):
        raise SystemExit(f"CX base price is not real: {cx_price}")

    kg = by_unit.get("kg") or []
    if not kg:
        raise SystemExit("fixture missing KG item")
    if str(kg[0].get("unidadeCanonica") or "") != "kg":
        raise SystemExit(f"KG canonical is not kg: {kg[0].get('unidadeCanonica')}")
    kg_price = parse_decimal(kg[0].get("valorPorUnidadeCanonica"))
    kg_unit = parse_decimal(kg[0].get("valorUnitario"))
    if kg_price is None or kg_unit is None or abs(kg_price - kg_unit) > Decimal("0.000001"):
        raise SystemExit(f"KG base price is not real: {kg_price}")

    grams = by_unit.get("g") or []
    if not grams:
        raise SystemExit("fixture missing G item")
    if str(grams[0].get("unidadeCanonica") or "") != "kg":
        raise SystemExit(f"G canonical is not kg: {grams[0].get('unidadeCanonica')}")
    g_price = parse_decimal(grams[0].get("valorPorUnidadeCanonica"))
    g_unit = parse_decimal(grams[0].get("valorUnitario"))
    if g_unit is None or g_price is None:
        raise SystemExit("G item missing prices")
    expected = (g_unit / Decimal("0.001")).quantize(Decimal("0.000001"))
    if abs(g_price - expected) > Decimal("0.000001"):
        raise SystemExit(f"G base price {g_price} != {expected}")
    if g_price == g_unit:
        raise SystemExit("G base price equals source price; factor was not applied")

    unknown = by_unit.get("foobar") or []
    if not unknown:
        raise SystemExit("fixture missing unknown unit item")
    if str(unknown[0].get("unidadeCanonica") or "") != "unknown":
        raise SystemExit(f"unknown unit was invented as {unknown[0].get('unidadeCanonica')}")
    if unknown[0].get("valorPorUnidadeCanonica") is not None:
        raise SystemExit("unknown unit invented a base-unit price")

    ch_cols = fact_columns(settings)
    if "unidade_canonica" not in ch_cols:
        raise SystemExit("clickhouse item_fact missing unidade_canonica")
    if "valor_unitario_base" not in ch_cols and "valor_por_unidade_canonica" not in ch_cols:
        raise SystemExit("clickhouse item_fact missing valor_por_unidade_canonica")
    facts = fetch_item_facts(settings)
    if not facts:
        raise SystemExit("clickhouse item_fact is empty")
    if all(row.get("unidade_canonica") in (None, "") for row in facts):
        raise SystemExit("clickhouse unidade_canonica always null")
    ch_prices = [
        row.get("valor_por_unidade_canonica")
        if row.get("valor_por_unidade_canonica") is not None
        else row.get("valor_unitario_base")
        for row in facts
    ]
    if all(v is None for v in ch_prices):
        raise SystemExit("clickhouse valor_por_unidade_canonica always null")
    fact_by_unit = {}
    for row in facts:
        fact_by_unit.setdefault(fold(row.get("unidade_medida")), []).append(row)
    if str((fact_by_unit.get("cx") or [{}])[0].get("unidade_canonica") or "") != "cx":
        raise SystemExit("clickhouse CX fact missing canonical cx")
    if str((fact_by_unit.get("foobar") or [{}])[0].get("unidade_canonica") or "") != "unknown":
        raise SystemExit("clickhouse invented a unit for FOOBAR")
    foobar_price = (fact_by_unit.get("foobar") or [{}])[0]
    if foobar_price.get("valor_por_unidade_canonica") is not None or foobar_price.get("valor_unitario_base") is not None:
        raise SystemExit("clickhouse invented a base price for unknown unit")


class _official_hosts_blocked:
    def __enter__(self):
        self._client = httpx.Client
        deny_resolve(True)

        class Guarded(httpx.Client):
            def request(self, method, url, *args, **kwargs):
                _fail_if_official_host(url)
                return super().request(method, url, *args, **kwargs)

            def stream(self, method, url, *args, **kwargs):
                _fail_if_official_host(url)
                return super().stream(method, url, *args, **kwargs)

        httpx.Client = Guarded
        return self

    def __exit__(self, exc_type, exc, tb):
        deny_resolve(False)
        httpx.Client = self._client
        if exc_type is RuntimeError and exc and (
            "fixture mode hit official host" in str(exc) or "fixture mode called" in str(exc)
        ):
            raise SystemExit(str(exc)) from exc
        return False


def _fail_if_official_host(url) -> None:
    host = (httpx.URL(str(url)).host or "").lower()
    if host in OFFICIAL_HOSTS or any(token in host for token in OFFICIAL_HOST_NEEDLES):
        raise RuntimeError(f"fixture mode hit official host {host}")


def _assert_refetch_schedule(settings: Settings) -> None:
    from compras_ingest.assets import (
        JOB_NAME,
        SCHEDULE_CRON,
        SCHEDULE_NAME,
        SCHEDULE_TZ,
        defs,
    )
    from compras_ingest.refetch import REFETCH_SOURCES
    from compras_ingest.settings import TRAILING_WINDOW_DAYS

    if settings.trailing_window_days != TRAILING_WINDOW_DAYS:
        raise SystemExit(f"trailing_window_days {settings.trailing_window_days} != {TRAILING_WINDOW_DAYS}")
    schedules = list(defs.schedules or [])
    found = next((s for s in schedules if s.name == SCHEDULE_NAME), None)
    if found is None:
        raise SystemExit(f"defs missing schedule {SCHEDULE_NAME}")
    if not found.cron_schedule:
        raise SystemExit("refetch schedule missing cron")
    if found.cron_schedule != SCHEDULE_CRON:
        raise SystemExit(f"refetch cron {found.cron_schedule} != {SCHEDULE_CRON}")
    if found.execution_timezone != SCHEDULE_TZ:
        raise SystemExit(f"refetch tz {found.execution_timezone} != {SCHEDULE_TZ}")
    target = found.job_name or getattr(found.job, "name", "")
    if target != JOB_NAME:
        raise SystemExit(f"schedule does not target {JOB_NAME}: {target}")
    job = defs.resolve_job_def(JOB_NAME)
    store = LandingStore(settings)
    before = {src: set(store.list_parquet(src)) for src in REFETCH_SOURCES}
    result = job.execute_in_process()
    if not result.success:
        raise SystemExit("trailing_window_refetch job failed")
    mid = {src: set(store.list_parquet(src)) for src in REFETCH_SOURCES}
    extra = {src: sorted(mid[src] - before[src]) for src in REFETCH_SOURCES if mid[src] - before[src]}
    if extra:
        raise SystemExit(f"refetch wrote new landing hashes: {extra}")
    result2 = job.execute_in_process()
    if not result2.success:
        raise SystemExit("second trailing_window_refetch job failed")
    after = {src: set(store.list_parquet(src)) for src in REFETCH_SOURCES}
    extra2 = {src: sorted(after[src] - mid[src]) for src in REFETCH_SOURCES if after[src] - mid[src]}
    if extra2:
        raise SystemExit(f"second refetch wrote new landing hashes: {extra2}")


def _assert_incremental_schedules(settings: Settings) -> None:
    from compras_ingest.assets import defs
    from compras_ingest.incremental import (
        DAILY_ASSET_KEYS,
        DAILY_CRON,
        DAILY_JOB_NAME,
        DAILY_SCHEDULE_NAME,
        MONTHLY_ASSET_KEYS,
        MONTHLY_CRON,
        MONTHLY_JOB_NAME,
        MONTHLY_SCHEDULE_NAME,
        SCHEDULE_TZ,
    )

    from dagster import DagsterInstance
    from compras_ingest.assets import _job_asset_keys

    _assert_fixture_fetch_off(settings)
    instance = DagsterInstance.ephemeral()
    jobs = []
    for name, cron, job_name, tz, need in (
        (DAILY_SCHEDULE_NAME, DAILY_CRON, DAILY_JOB_NAME, SCHEDULE_TZ, set(DAILY_ASSET_KEYS)),
        (MONTHLY_SCHEDULE_NAME, MONTHLY_CRON, MONTHLY_JOB_NAME, SCHEDULE_TZ, set(MONTHLY_ASSET_KEYS)),
    ):
        found = next((s for s in (defs.schedules or []) if s.name == name), None)
        if found is None:
            raise SystemExit(f"defs missing schedule {name}")
        if not found.cron_schedule:
            raise SystemExit(f"{name} missing cron")
        if found.cron_schedule != cron:
            raise SystemExit(f"{name} cron {found.cron_schedule} != {cron}")
        if found.execution_timezone != tz:
            raise SystemExit(f"{name} tz {found.execution_timezone} != {tz}")
        target = found.job_name or getattr(found.job, "name", "")
        if target != job_name:
            raise SystemExit(f"{name} does not target {job_name}: {target}")
        job = defs.resolve_job_def(job_name)
        selected = _job_asset_keys(job)
        if not selected:
            raise SystemExit(f"{job_name} has no asset selection")
        if not need.issubset(selected):
            raise SystemExit(f"{job_name} missing land assets {need - selected}")
        jobs.append(job)
    for job in jobs:
        before = _landing_digests(settings)
        result = job.execute_in_process(instance=instance)
        if not result.success:
            raise SystemExit(f"{job.name} failed")
        mid = _landing_digests(settings)
        if mid != before:
            raise SystemExit(f"{job.name} changed landing content hashes")
        result2 = job.execute_in_process(instance=instance)
        if not result2.success:
            raise SystemExit(f"second {job.name} failed")
        after = _landing_digests(settings)
        if after != mid:
            raise SystemExit(f"second {job.name} changed landing content hashes")


def _assert_nightly_detector_schedule(settings: Settings) -> None:
    from dagster import DagsterInstance

    from compras_ingest.assets import _job_asset_keys, defs
    from compras_ingest.detect_schedule import (
        ASSET_KEYS,
        JOB_NAME,
        SCHEDULE_CRON,
        SCHEDULE_NAME,
        SCHEDULE_TZ,
    )

    if SCHEDULE_TZ != "America/Sao_Paulo":
        raise SystemExit(f"nightly detector tz is {SCHEDULE_TZ}")
    if SCHEDULE_CRON != "0 6 * * *":
        raise SystemExit(f"nightly detector cron {SCHEDULE_CRON} != 0 6 * * *")
    found = next((s for s in (defs.schedules or []) if s.name == SCHEDULE_NAME), None)
    if found is None:
        raise SystemExit(f"defs missing schedule {SCHEDULE_NAME}")
    if not found.cron_schedule:
        raise SystemExit("nightly detector schedule missing cron")
    if found.cron_schedule != SCHEDULE_CRON:
        raise SystemExit(f"nightly detector cron {found.cron_schedule} != {SCHEDULE_CRON}")
    if found.execution_timezone != SCHEDULE_TZ:
        raise SystemExit(f"nightly detector tz is {found.execution_timezone} not {SCHEDULE_TZ}")
    target = found.job_name or getattr(found.job, "name", "")
    if target != JOB_NAME:
        raise SystemExit(f"nightly detector schedule does not target {JOB_NAME}: {target}")
    job = defs.resolve_job_def(JOB_NAME)
    selected = _job_asset_keys(job)
    need = set(ASSET_KEYS)
    if not selected:
        raise SystemExit(f"{JOB_NAME} has no asset selection")
    if not need.issubset(selected):
        raise SystemExit(f"{JOB_NAME} missing detect assets {need - selected}")
    if selected - need:
        raise SystemExit(f"{JOB_NAME} selected extra assets {selected - need}")
    if "warehouse_entities" in selected:
        raise SystemExit(f"{JOB_NAME} must not rematerialize warehouse_entities")
    before = fetch_counts(settings)
    before_flags = {str(row["id"]) for row in fetch_flags(settings)}
    if before["flag"] < 1:
        raise SystemExit("nightly detector e2e expected seed flags before rematerialize")
    instance = DagsterInstance.ephemeral()
    result = job.execute_in_process(instance=instance)
    if not result.success:
        raise SystemExit(f"{JOB_NAME} failed")
    mid = fetch_counts(settings)
    mid_flags = {str(row["id"]) for row in fetch_flags(settings)}
    _assert_same_detect_counts(before, mid, f"{JOB_NAME}")
    if mid_flags != before_flags:
        raise SystemExit(f"{JOB_NAME} changed flag ids")
    result2 = job.execute_in_process(instance=instance)
    if not result2.success:
        raise SystemExit(f"second {JOB_NAME} failed")
    after = fetch_counts(settings)
    after_flags = {str(row["id"]) for row in fetch_flags(settings)}
    _assert_same_detect_counts(mid, after, f"second {JOB_NAME}")
    if after_flags != mid_flags:
        raise SystemExit(f"second {JOB_NAME} changed flag ids")


def _assert_same_detect_counts(before: dict[str, int], after: dict[str, int], label: str) -> None:
    for table in ("flag", "fornecedor_adjacency", "co_bid_edge", "co_bid_screen"):
        if after[table] != before[table]:
            raise SystemExit(f"{label} changed {table} count {before[table]} -> {after[table]}")


def _assert_land_idempotency(settings: Settings) -> None:
    _assert_fixture_fetch_off(settings)
    store = LandingStore(settings)
    before_digests = _landing_digests(settings)
    before_counts = fetch_counts(settings)
    before_hashes = fetch_record_hashes(settings)
    before_facts = fetch_fact_count(settings)
    _reland_all(settings, store)
    mid_digests = _landing_digests(settings)
    _assert_same_landing(before_digests, mid_digests, "first reland")
    _reland_all(settings, store)
    after_digests = _landing_digests(settings)
    _assert_same_landing(mid_digests, after_digests, "second reland")
    after_counts = fetch_counts(settings)
    after_hashes = fetch_record_hashes(settings)
    after_facts = fetch_fact_count(settings)
    grown = {k: (before_counts[k], after_counts[k]) for k in before_counts if after_counts[k] > before_counts[k]}
    if grown:
        raise SystemExit(f"warehouse row counts grew after idempotent land: {grown}")
    extra_hashes = after_hashes - before_hashes
    if extra_hashes:
        raise SystemExit(f"warehouse record hashes grew after idempotent land: {len(extra_hashes)}")
    if after_facts > before_facts:
        raise SystemExit(f"item_fact FINAL count grew {before_facts} -> {after_facts}")


def _assert_fixture_fetch_off(settings: Settings) -> None:
    if settings.compras_gov_fetch:
        raise SystemExit("fixture e2e must run with COMPRAS_GOV_FETCH=0")
    if settings.tce_rs_fetch:
        raise SystemExit("fixture e2e must run with TCE_RS_FETCH=0")
    if settings.sanctions_fetch:
        raise SystemExit("fixture e2e must run with SANCTIONS_FETCH=0")
    if settings.ocds_fetch or settings.receita_cnpj_fetch or settings.pncp_consulta_fetch or settings.tce_sp_fetch:
        raise SystemExit("fixture e2e must keep official fetch flags off")


def _reland_all(settings: Settings, store: LandingStore) -> None:
    land_catalogo_cnbs(settings, store)
    land_compras_gov(settings, store)
    basicos: set[str] = set()
    for key in store.list_parquet("compras_gov"):
        basicos |= cnpj_basicos_from_frame(store.read_parquet(key))
    land_receita_cnpj(settings, store, cnpj_basicos=basicos)
    land_ocds(settings, store=store)
    land_pncp_consulta(settings, store)
    land_tce_sp_licitacao(settings, store)
    land_tce_rs_licitacon(settings, store)
    land_cgu_ceis_cnep(settings, store)


def _landing_digests(settings: Settings) -> dict[str, dict[str, str]]:
    store = LandingStore(settings)
    out: dict[str, dict[str, str]] = {}
    for source in (
        "compras_gov",
        "catalogo_cnbs",
        "ocds",
        "receita_cnpj",
        "receita_cnpj_socios",
        "pncp_consulta",
        TCE_SP_SOURCE,
        TCE_RS_SOURCE,
        CGU_SOURCE,
    ):
        out[source] = {}
        for key in store.list_parquet(source):
            if not key.endswith(".parquet"):
                continue
            out[source][key] = sha256_bytes(store.get(key))
    return out


def _assert_same_landing(before: dict[str, dict[str, str]], after: dict[str, dict[str, str]], label: str) -> None:
    if after.keys() != before.keys():
        raise SystemExit(f"{label} landing sources drifted: {sorted(after)} vs {sorted(before)}")
    for source, first in before.items():
        second = after[source]
        if set(second) != set(first):
            raise SystemExit(f"{label} {source} parquet keys drifted: {sorted(second)} vs {sorted(first)}")
        for key, digest in first.items():
            if second[key] != digest:
                raise SystemExit(f"{label} {source} {key} sha256 changed")


def _assert_retroactive_edit_flags(items, flags, stored, hashes_before, store) -> None:
    expected = _load_retroactive_edit_expected()
    want = set(expected["flag"])
    absent = set(expected["absent"])
    if want != set(EDIT_FLAG_IDS) or absent != set(EDIT_ABSENT_IDS):
        raise SystemExit("retroactive_edit expected.json drifted from planted ids")
    planted = want | absent
    have_items = {str(v) for v in items["record_id"].to_list()}
    missing_items = planted - have_items
    if missing_items:
        raise SystemExit(f"retroactive_edit plants missing from normalized items: {sorted(missing_items)}")

    got: dict[str, dict] = {}
    for row in flags.iter_rows(named=True):
        if str(row.get("kind") or "") != EDIT_KIND:
            continue
        rid = str(row.get("record_id") or "")
        delta = _parse_edit_delta(row.get("delta"))
        got[rid] = delta
    extra = set(got) - want
    missing = want - set(got)
    leaked = set(got) & absent
    if extra or missing or leaked:
        raise SystemExit(
            f"retroactive_edit record_ids extra={sorted(extra)} missing={sorted(missing)} leaked={sorted(leaked)}"
        )
    for rid, spec in expected["flag"].items():
        delta = got[rid]
        field = spec["field"]
        fields = delta.get("fields") or {}
        if field not in fields:
            raise SystemExit(f"{rid} delta missing {field}: {delta}")
        pair = fields[field]
        if parse_decimal(pair.get("before")) != parse_decimal(spec["before"]):
            raise SystemExit(f"{rid} before {pair.get('before')} != {spec['before']}")
        if field == "fornecedor_cnpj":
            if str(pair.get("before") or "") != spec["before"] or str(pair.get("after") or "") != spec["after"]:
                raise SystemExit(f"{rid} cnpj diff drifted: {pair}")
        elif parse_decimal(pair.get("after")) != parse_decimal(spec["after"]):
            raise SystemExit(f"{rid} after {pair.get('after')} != {spec['after']}")
        if not delta.get("old_hash") or not delta.get("new_hash"):
            raise SystemExit(f"{rid} delta missing hashes: {delta}")
        if delta.get("old_hash") == delta.get("new_hash"):
            raise SystemExit(f"{rid} old_hash equals new_hash")
        if not delta.get("old_snapshot_id") or not delta.get("new_snapshot_id"):
            raise SystemExit(f"{rid} delta missing snapshot ids: {delta}")

    hashes_after = {Path(k).stem for k in store.list_parquet("compras_gov")}
    if not (hashes_after - hashes_before):
        raise SystemExit("second landing wrote no new compras_gov hash")

    id_to_rid = {
        item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or "")): str(row.get("record_id") or "")
        for row in items.iter_rows(named=True)
    }
    ware: dict[str, dict] = {}
    for row in stored:
        if str(row.get("kind") or "") != EDIT_KIND:
            continue
        if str(row.get("state") or "") != "detected":
            raise SystemExit(f"retroactive_edit state is not detected: {row.get('state')}")
        if row.get("publishedAt") not in (None, ""):
            raise SystemExit(f"retroactive_edit publishedAt is set: {row.get('publishedAt')}")
        rid = id_to_rid.get(str(row.get("itemId") or ""))
        if not rid:
            raise SystemExit(f"retroactive_edit itemId not in slice: {row.get('itemId')}")
        ware[rid] = _parse_edit_delta(row.get("delta"))
    if set(ware) != want:
        raise SystemExit(f"warehouse retroactive_edit ids {sorted(ware)} != planted {sorted(want)}")
    if set(ware) & absent:
        raise SystemExit(f"warehouse flagged silent retroactive_edit plants {sorted(set(ware) & absent)}")
    for rid, spec in expected["flag"].items():
        fields = (ware[rid].get("fields") or {})
        if spec["field"] not in fields:
            raise SystemExit(f"warehouse {rid} delta missing {spec['field']}: {ware[rid]}")


def _assert_receita_adjacency(settings: Settings) -> None:
    expected = load_adjacency_expected()
    want = {
        (str(row["kind"]), str(row["leftCnpj"]), str(row["rightCnpj"]))
        for row in expected["edges"]
    }
    stored = fetch_adjacencies(settings)
    got = {
        (str(row["kind"]), str(row["leftCnpj"]), str(row["rightCnpj"]))
        for row in stored
    }
    if got != want:
        raise SystemExit(f"fornecedor_adjacency {sorted(got)} != planted {sorted(want)}")
    for cnpj in expected["clean"]:
        hits = [row for row in stored if cnpj in (row["leftCnpj"], row["rightCnpj"])]
        if hits:
            raise SystemExit(f"clean CNPJ {cnpj} has edges {hits}")
    forbidden = [str(v) for v in expected.get("raw_cpf_forbidden") or []]
    masked = str(expected.get("partner_cpf_masked") or "")
    partner_cnpj = str(expected.get("partner_cnpj") or "")
    partner_evidence = [
        str(row.get("evidence") or "")
        for row in stored
        if str(row.get("kind") or "") == "shared_qsa_partner"
    ]
    if masked and not any(masked in text for text in partner_evidence):
        raise SystemExit("shared_qsa_partner evidence missing masked CPF")
    if partner_cnpj and not any(partner_cnpj in text for text in partner_evidence):
        raise SystemExit("shared_qsa_partner evidence missing legal-entity socio CNPJ")
    for row in stored:
        if str(row.get("leftCnpj") or "") >= str(row.get("rightCnpj") or ""):
            raise SystemExit("adjacency pair is not stored leftCnpj < rightCnpj")
        if not row.get("snapshotId"):
            raise SystemExit("adjacency missing snapshotId")
        if not row.get("methodologyVersion"):
            raise SystemExit("adjacency missing methodologyVersion")
        if not row.get("evidence"):
            raise SystemExit("adjacency missing evidence")
        blobs = [
            str(row.get("evidence") or ""),
            str(row.get("leftCnpj") or ""),
            str(row.get("rightCnpj") or ""),
        ]
        assert_no_raw_cpf(blobs)
        for raw in forbidden:
            if raw and raw in " ".join(blobs):
                raise SystemExit(f"adjacency stored raw CPF {raw}")


def _assert_fornecedor_receita_facts(settings: Settings) -> None:
    papel = "11222333000181"
    financeira = "44555666000172"
    socios = fetch_fornecedor_socios(settings, cnpj=papel)
    names = {str(row.get("nome") or "") for row in socios}
    if names != {"JOAO DA SILVA", "EDITORA EXEMPLO LTDA"}:
        raise SystemExit(f"papelaria QSA {sorted(names)} != planted PF+PJ pair")
    joao = next(row for row in socios if row.get("nome") == "JOAO DA SILVA")
    if str(joao.get("cpfMasked") or "") != mask_cpf(RAW_CPF):
        raise SystemExit(f"JOAO CPF not ingest-masked: {joao.get('cpfMasked')}")
    if str(joao.get("qualificacao") or "") != "Sócio-Administrador":
        raise SystemExit(f"JOAO qualificacao drifted: {joao.get('qualificacao')}")
    editora = next(row for row in socios if row.get("nome") == "EDITORA EXEMPLO LTDA")
    if editora.get("cpfMasked") not in (None, ""):
        raise SystemExit(f"PJ socio stored a CPF: {editora.get('cpfMasked')}")
    if str(editora.get("qualificacao") or "") != "Sócio":
        raise SystemExit(f"EDITORA qualificacao drifted: {editora.get('qualificacao')}")
    if fetch_fornecedor_socios(settings, cnpj=financeira):
        raise SystemExit("financeira QSA is not empty")
    cnaes = {str(row["codigo"]): str(row["descricao"]) for row in fetch_cnaes(settings)}
    want_cnae = "Comércio varejista de livros, jornais, revistas e papelaria"
    if cnaes.get("4761001") != want_cnae:
        raise SystemExit(f"cnae 4761001 drifted: {cnaes.get('4761001')}")
    blobs = [str(value) for row in socios for value in row.values() if value is not None]
    assert_no_raw_cpf(blobs)
    if RAW_CPF in " ".join(blobs):
        raise SystemExit("warehouse socio stored raw CPF")


def _assert_cobid_suite(settings: Settings) -> None:
    expected = load_cobid_expected()
    thresh = load_cade_thresholds()
    if not thresh:
        raise SystemExit("cade_screens.csv is empty")
    parts = fetch_participants(settings)
    if not parts:
        raise SystemExit("licitacao_participante is empty")
    by_lic = {str(row.get("licitacaoId") or "") for row in parts}
    for lid in expected["cover_licitacoes"] + expected["rotation_licitacoes"] + ["VARIANCE", "SKEW", "CLEAN", "CPFONLY"]:
        if lid not in by_lic:
            raise SystemExit(f"warehouse missing planted licitacao {lid}")
    if expected["other_uf"] in by_lic:
        raise SystemExit("OTHER-UF participant was persisted")
    ufs = {str(row.get("uf") or "") for row in parts}
    sources = {str(row.get("source") or "") for row in parts}
    if ufs - {"SP", "RS"}:
        raise SystemExit(f"participant uf outside SP/RS: {sorted(ufs)}")
    if sources - {"tce_sp", "tce_rs"}:
        raise SystemExit(f"participant source not tce_sp/tce_rs: {sorted(sources)}")
    landing_sp = [r for r in parts if r.get("source") == "tce_sp" and "34914897000180" in str(r.get("participante") or "")]
    landing_rs = [r for r in parts if r.get("source") == "tce_rs" and "03722885000120" in str(r.get("participante") or "")]
    if not landing_sp:
        raise SystemExit("warehouse dropped TCE-SP landing participant")
    if not landing_rs:
        raise SystemExit("warehouse dropped TCE-RS landing participant")
    cpf_rows = [r for r in parts if str(r.get("licitacaoId") or "") == expected["cpf_licitacao"]]
    if not cpf_rows:
        raise SystemExit("warehouse missing CPFONLY participante")
    if any(expected["cpf_masked"] not in str(r.get("participante") or "") for r in cpf_rows):
        raise SystemExit("CPFONLY participante is not masked")
    forbidden = [str(v) for v in expected.get("cpf_raw_forbidden") or []]
    for row in parts:
        blobs = [str(v) for v in row.values() if v is not None]
        assert_no_raw_cpf(blobs)
        for raw in forbidden:
            if raw and raw in " ".join(blobs):
                raise SystemExit(f"participante stored raw CPF {raw}")
    screens = fetch_cobid_screens(settings)
    got: dict[str, set[str]] = {}
    for row in screens:
        kind = str(row.get("kind") or "")
        got.setdefault(kind, set()).add(str(row.get("subjectId") or ""))
        if str(row.get("state") or "") != "detected":
            raise SystemExit(f"cobid screen state is not detected: {row.get('state')}")
        if str(row.get("methodologyVersion") or "") != settings.methodology_version:
            raise SystemExit(f"cobid screen methodologyVersion {row.get('methodologyVersion')!r}")
        evidence = str(row.get("evidence") or "")
        if "indicio a verificar" not in evidence:
            raise SystemExit(f"cobid screen missing framing: {evidence}")
        assert_no_raw_cpf([evidence])
        for raw in forbidden:
            if raw and raw in evidence:
                raise SystemExit(f"cobid evidence stored raw CPF {raw}")
    want = {
        KIND_VARIANCE: set(expected["bid_variance"]),
        KIND_SKEW: set(expected["skew"]),
        KIND_COVER: set(expected["cover_bidding"]),
        KIND_ROTATION: set(expected["winner_rotation"]),
    }
    for kind, ids in want.items():
        have = got.get(kind, set())
        if have != ids:
            raise SystemExit(f"{kind} subjects {sorted(have)} != planted {sorted(ids)}")
    absent = set(expected["absent"])
    flagged = {sid for ids in got.values() for sid in ids}
    leaked = absent & flagged
    if leaked:
        raise SystemExit(f"clean/other-uf screens leaked: {sorted(leaked)}")
    extra = flagged - {sid for ids in want.values() for sid in ids}
    if extra:
        raise SystemExit(f"unexpected cobid subjects {sorted(extra)}")
    edges = fetch_cobid_edges(settings)
    if not edges:
        raise SystemExit("co_bid_edge is empty")
    cover_ids = set(expected["cover_licitacoes"])
    if not any(e.get("licitacaoId") in cover_ids for e in edges):
        raise SystemExit("missing COVER co_bid edges")
    for row in edges:
        left = str(row.get("leftCnpj") or "")
        right = str(row.get("rightCnpj") or "")
        if str(row.get("kind") or "") != "co_bid":
            raise SystemExit(f"co_bid edge kind is not co_bid: {row.get('kind')}")
        if not is_cnpj(left) or not is_cnpj(right):
            raise SystemExit(f"co_bid edge is not CNPJ-CNPJ: {left} {right}")
        if left >= right:
            raise SystemExit("co_bid pair is not stored leftCnpj < rightCnpj")
        if expected["other_uf"] in str(row.get("licitacaoId") or ""):
            raise SystemExit("OTHER-UF produced a co_bid edge")
        if str(row.get("licitacaoId") or "") == expected["cpf_licitacao"]:
            raise SystemExit("CPFONLY produced a co_bid edge")
        if "***" in left or "***" in right:
            raise SystemExit(f"co_bid edge stored masked CPF: {left} {right}")
        assert_no_raw_cpf([str(v) for v in row.values() if v is not None])
        for raw in forbidden:
            if raw and raw in " ".join([left, right]):
                raise SystemExit(f"co_bid edge stored raw CPF {raw}")


def _load_retroactive_edit_expected() -> dict:
    from compras_detect.tier1.retroactive_edit import fixture_dir

    path = fixture_dir() / "expected.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_edit_delta(raw) -> dict:
    text = str(raw or "")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"retroactive_edit delta is not JSON: {text}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"retroactive_edit delta is not an object: {text}")
    return payload


def _check_defs() -> None:
    from compras_ingest.assets import assert_asset_graph

    try:
        assert_asset_graph()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


def _assert_official_urls(settings: Settings) -> dict:
    try:
        ocds = fixture_ocds_official(settings.ocds_year)
        rfb = fixture_receita_official()
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
    try:
        pncp = fixture_pncp_official()
    except Exception as exc:
        raise SystemExit(f"official URL resolve failed: {exc}") from exc
    if pncp.consulta_base != PNCP_CONSULTA_BASE:
        raise SystemExit(f"PNCP consulta base is not official: {pncp.consulta_base}")
    if pncp.consulta_openapi != PNCP_CONSULTA_OPENAPI:
        raise SystemExit(f"PNCP consulta OpenAPI is not official: {pncp.consulta_openapi}")
    if "pncp.gov.br" not in pncp.consulta_base or "pncp.gov.br" not in pncp.api_base:
        raise SystemExit(f"PNCP host is not official: {pncp.consulta_base} {pncp.api_base}")
    if pncp.api_base != PNCP_API_BASE:
        raise SystemExit(f"PNCP items API base is not official: {pncp.api_base}")
    if pncp.swagger_url != PNCP_CONSULTA_SWAGGER:
        raise SystemExit(f"PNCP swagger URL is not official: {pncp.swagger_url}")
    if pncp.publicacao_path != PNCP_PUBLICACAO_PATH or pncp.compra_path != PNCP_COMPRA_PATH:
        raise SystemExit("PNCP consulta paths are not the live OpenAPI paths")
    if pncp.itens_path != PNCP_ITENS_PATH or pncp.resultados_path != PNCP_ITEM_RESULTADOS_PATH:
        raise SystemExit("PNCP items paths are not the live OpenAPI paths")
    if not pncp.modalidades:
        raise SystemExit("PNCP modalidades resolved empty")
    try:
        tce = fixture_tce_sp_official(settings.tce_sp_year, settings.tce_sp_month)
    except Exception as exc:
        raise SystemExit(f"official URL resolve failed: {exc}") from exc
    if tce.listing_url != TCE_SP_LISTING_URL:
        raise SystemExit(f"TCE-SP listing URL is not official: {tce.listing_url}")
    if "transparencia.tce.sp.gov.br" not in tce.zip_url:
        raise SystemExit(f"TCE-SP zip host is not official: {tce.zip_url}")
    if "/licitacoes-contratos/licitacao-" not in tce.zip_url:
        raise SystemExit(f"TCE-SP download is not a licitacao zip: {tce.zip_url}")
    if "cubo" in tce.zip_url.lower():
        raise SystemExit(f"TCE-SP cubo SQL is not the licitacao extract: {tce.zip_url}")
    if f"licitacao-{settings.tce_sp_year}-{settings.tce_sp_month:02d}" not in tce.zip_url:
        raise SystemExit(f"TCE-SP zip is not the requested year/month: {tce.zip_url}")
    _assert_tce_sp_host_refused()
    try:
        tce_rs = fixture_tce_rs_official(settings.tce_rs_year)
    except Exception as exc:
        raise SystemExit(f"official URL resolve failed: {exc}") from exc
    if tce_rs.portal_url != tce_rs_portal_url(settings.tce_rs_year):
        raise SystemExit(f"TCE-RS portal URL is not official: {tce_rs.portal_url}")
    if tce_rs.ckan_url != tce_rs_ckan_url(settings.tce_rs_year):
        raise SystemExit(f"TCE-RS CKAN URL is not official: {tce_rs.ckan_url}")
    if tce_rs.example_url != TCE_RS_EXAMPLE_URL:
        raise SystemExit(f"TCE-RS example remessa URL is not official: {tce_rs.example_url}")
    if tce_rs.leiaute_url != TCE_RS_LEIAUTE_URL:
        raise SystemExit(f"TCE-RS leiaute URL is not official: {tce_rs.leiaute_url}")
    if tce_rs.zip_url != TCE_RS_EXAMPLE_URL:
        raise SystemExit(f"default TCE-RS zip is not the official example remessa: {tce_rs.zip_url}")
    if "dados.tce.rs.gov.br" not in tce_rs.ckan_url:
        raise SystemExit(f"TCE-RS CKAN host is not official: {tce_rs.ckan_url}")
    if "tcers.tc.br" not in tce_rs.example_url or "tcers.tc.br" not in tce_rs.leiaute_url:
        raise SystemExit("TCE-RS example or leiaute host is not official")
    _assert_tce_rs_host_refused()
    try:
        cgu = fixture_cgu_ceis_cnep_official()
    except Exception as exc:
        raise SystemExit(f"official URL resolve failed: {exc}") from exc
    if settings.sanctions_fetch:
        raise SystemExit("fixture e2e must run with SANCTIONS_FETCH=0")
    if cgu.listing_ceis != CGU_CEIS_LISTING_URL:
        raise SystemExit(f"CEIS listing URL is not official: {cgu.listing_ceis}")
    if cgu.listing_cnep != CGU_CNEP_LISTING_URL:
        raise SystemExit(f"CNEP listing URL is not official: {cgu.listing_cnep}")
    if "portaldatransparencia.gov.br" not in cgu.ceis_download_url:
        raise SystemExit(f"CEIS download host is not official: {cgu.ceis_download_url}")
    if "portaldatransparencia.gov.br" not in cgu.cnep_download_url:
        raise SystemExit(f"CNEP download host is not official: {cgu.cnep_download_url}")
    if "dadosabertos-download.cgu.gov.br" not in cgu.ceis_zip_url:
        raise SystemExit(f"CEIS zip host is not official: {cgu.ceis_zip_url}")
    if "dadosabertos-download.cgu.gov.br" not in cgu.cnep_zip_url:
        raise SystemExit(f"CNEP zip host is not official: {cgu.cnep_zip_url}")
    if "/download-de-dados/ceis/" not in cgu.ceis_download_url:
        raise SystemExit(f"CEIS download is not the Portal dated path: {cgu.ceis_download_url}")
    if "/download-de-dados/cnep/" not in cgu.cnep_download_url:
        raise SystemExit(f"CNEP download is not the Portal dated path: {cgu.cnep_download_url}")
    _assert_cgu_host_refused()
    return {
        "ocds_jsonl": ocds.jsonl_url,
        "rfb_index": rfb.index_url,
        "rfb_month": rfb.month,
        "pncp_consulta": pncp.consulta_base,
        "pncp_openapi": pncp.consulta_openapi,
        "tce_sp_zip": tce.zip_url,
        "tce_rs_zip": tce_rs.zip_url,
        "cgu_ceis_zip": cgu.ceis_zip_url,
        "cgu_cnep_zip": cgu.cnep_zip_url,
    }


def _assert_coverage_warehouse(settings: Settings) -> None:
    catalog = fetch_catalog_codes(settings)
    if len(catalog) < 1:
        raise SystemExit("warehouse missing catalog_code after land")
    kinds = {str(row.get("kind") or "") for row in catalog}
    if "catmat" not in kinds:
        raise SystemExit("catalog_code missing catmat after land")
    sources = {str(row.get("name") or ""): row for row in fetch_landing_sources(settings)}
    for name in ("compras_gov", "receita_cnpj", "ocds", "pncp_consulta", "tce_sp", "tce_rs", "cgu_ceis_cnep"):
        row = sources.get(name)
        if row is None:
            raise SystemExit(f"landing_source missing {name}")
        if int(row.get("n") or 0) < 1:
            raise SystemExit(f"landing_source {name} n=0 after land")
        if row.get("lastUpdate") is None:
            raise SystemExit(f"landing_source {name} lastUpdate is null after land")


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


def _assert_compras_gov_official_urls(settings: Settings) -> None:
    for year in settings.compras_gov_years:
        official = fixture_compras_gov_official(year, settings.compras_gov_base.rstrip("/"))
        if official.index_url != COMPRAS_GOV_INDEX:
            raise SystemExit(f"Compras.gov index is not official: {official.index_url}")
        if official.cadence != "anual":
            raise SystemExit(f"Compras.gov {year} cadence is not anual: {official.cadence}")
        if f"/anual/{year}/comprasGOV-anual-VW_FT_PNCP_COMPRA-{year}.csv" not in official.compra_url:
            raise SystemExit(f"COMPRA URL is not the official anual file: {official.compra_url}")
        if f"/anual/{year}/comprasGOV-anual-VW_FT_PNCP_COMPRA_ITEM-{year}.csv" not in official.item_url:
            raise SystemExit(f"ITEM URL is not the official anual file: {official.item_url}")
        if "COMPRA_ITEM" in official.compra_url.rsplit("/", 1)[-1]:
            raise SystemExit(f"COMPRA URL pointed at ITEM: {official.compra_url}")
        assert_official_host(official.compra_url, COMPRAS_GOV_HOSTS)
        assert_official_host(official.item_url, COMPRAS_GOV_HOSTS)
    day = date(2026, 7, 15)
    diario = fixture_compras_gov_diario_official(day, settings.compras_gov_base.rstrip("/"))
    if diario.cadence != "diario":
        raise SystemExit(f"Compras.gov diario cadence is not diario: {diario.cadence}")
    if f"/diario/2026/07/15/comprasGOV-diario-VW_FT_PNCP_COMPRA-{day.isoformat()}.csv" not in diario.compra_url:
        raise SystemExit(f"COMPRA URL is not the official diario file: {diario.compra_url}")
    if f"/diario/2026/07/15/comprasGOV-diario-VW_FT_PNCP_COMPRA_ITEM-{day.isoformat()}.csv" not in diario.item_url:
        raise SystemExit(f"ITEM URL is not the official diario file: {diario.item_url}")
    mensal = fixture_compras_gov_mensal_official(2026, 7, settings.compras_gov_base.rstrip("/"))
    if mensal.cadence != "mensal":
        raise SystemExit(f"Compras.gov mensal cadence is not mensal: {mensal.cadence}")
    if "/mensal/2026/07/comprasGOV-mensal-VW_FT_PNCP_COMPRA-2026-07.csv" not in mensal.compra_url:
        raise SystemExit(f"COMPRA URL is not the official mensal file: {mensal.compra_url}")
    if "/mensal/2026/07/comprasGOV-mensal-VW_FT_PNCP_COMPRA_ITEM-2026-07.csv" not in mensal.item_url:
        raise SystemExit(f"ITEM URL is not the official mensal file: {mensal.item_url}")


def _assert_compras_gov_years(settings: Settings) -> None:
    store = LandingStore(settings)
    year_keys = store.year_partition_keys("compras_gov")
    if not year_keys:
        raise SystemExit("compras_gov landing has no year= partitions")
    for year in (2024, 2025, 2026):
        found = [k for k in year_keys if f"year={year}" in k]
        if not found:
            raise SystemExit(f"compras_gov missing year={year} parquet")
        if not any("date=" in k for k in found):
            raise SystemExit(f"compras_gov year={year} is not also partitioned by date")
    anos = set(fetch_contratacao_anos(settings))
    missing = {2024, 2025, 2026} - anos
    if missing:
        raise SystemExit(f"warehouse contratacao missing years {sorted(missing)}: {sorted(anos)}")


def _assert_compras_gov_fetch_anual_year_columns(settings: Settings) -> None:
    if settings.compras_gov_fetch:
        raise SystemExit("fixture e2e must run with COMPRAS_GOV_FETCH=0")
    root = Path(tempfile.mkdtemp(prefix="compras-gov-anual-fetch-"))
    planted = _plant_oficial_anual_year_column_files(root / "oficial")
    local = replace(
        settings,
        landing_uri=str(root / "landing"),
        compras_gov_fetch=True,
        trailing_window_as_of=date(2026, 8, 20),
    )
    transport = httpx.MockTransport(lambda request: _compras_gov_planted_response(request, planted))
    real_client = httpx.Client

    class PlantedClient(real_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    httpx.Client = PlantedClient
    try:
        land_compras_gov(local)
        _assert_planted_anual_partitions(local)
    finally:
        httpx.Client = real_client


def _plant_oficial_anual_year_column_files(root: Path) -> Path:
    # Official 2024 COMPRA uses ano_compra. 2025+ COMPRA uses ano_compra_pncp.
    # Plant both on 2024 so a split by anocomprapncp would drop year=2024.
    rows = {
        2024: (
            "id_compra,unidade_orgao_codigo_ibge,orgao_entidade_esfera_id,orgao_entidade_poder_id,ano_compra,ano_compra_pncp,data_publicacao_pncp,orgao_entidade_cnpj,orgao_entidade_razao_social,numero_controle_PNCP,objeto_compra,modalidade_nome\n"
            f"{FETCH_ANUAL_2024},3306305,M,E,2024,2025,2024-03-15,29477000000180,PREFEITURA MUNICIPAL DE VOLTA REDONDA,29477000000180-1-2024-00FETCH,Aquisicao planted 2024,Pregao Eletronico\n",
            "id_compra,id_compra_item,numero_item_compra,descricao,ano_compra\n"
            f"{FETCH_ANUAL_2024},{FETCH_ANUAL_2024}-1,1,Papel A4 planted 2024,2024\n",
        ),
        2025: (
            "id_compra,unidade_orgao_codigo_ibge,orgao_entidade_esfera_id,orgao_entidade_poder_id,ano_compra_pncp,data_publicacao_pncp,orgao_entidade_cnpj,orgao_entidade_razao_social,numero_controle_PNCP,objeto_compra,modalidade_nome\n"
            f"{FETCH_ANUAL_2025},3306305,M,E,2025,2025-04-15,29477000000180,PREFEITURA MUNICIPAL DE VOLTA REDONDA,29477000000180-1-2025-00FETCH,Aquisicao planted 2025,Pregao Eletronico\n",
            "id_compra,id_compra_item,numero_item_compra,descricao,ano_compra\n"
            f"{FETCH_ANUAL_2025},{FETCH_ANUAL_2025}-1,1,Papel A4 planted 2025,2025\n",
        ),
        2026: (
            "id_compra,unidade_orgao_codigo_ibge,orgao_entidade_esfera_id,orgao_entidade_poder_id,ano_compra_pncp,data_publicacao_pncp,orgao_entidade_cnpj,orgao_entidade_razao_social,numero_controle_PNCP,objeto_compra,modalidade_nome\n"
            f"{FETCH_ANUAL_2026},3306305,M,E,2026,2026-02-15,29477000000180,PREFEITURA MUNICIPAL DE VOLTA REDONDA,29477000000180-1-2026-00FETCH,Aquisicao planted 2026,Pregao Eletronico\n",
            "id_compra,id_compra_item,numero_item_compra,descricao,ano_compra\n"
            f"{FETCH_ANUAL_2026},{FETCH_ANUAL_2026}-1,1,Papel A4 planted 2026,2026\n",
        ),
    }
    for year, (compra, item) in rows.items():
        folder = root / "anual" / str(year)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"comprasGOV-anual-VW_FT_PNCP_COMPRA-{year}.csv").write_text(compra, encoding="utf-8")
        (folder / f"comprasGOV-anual-VW_FT_PNCP_COMPRA_ITEM-{year}.csv").write_text(item, encoding="utf-8")
    return root


def _compras_gov_planted_response(request: httpx.Request, planted: Path) -> httpx.Response:
    url = str(request.url)
    assert_official_host(url, COMPRAS_GOV_HOSTS)
    path = httpx.URL(url).path or ""
    if "/diario/" in path or "/mensal/" in path:
        return httpx.Response(404, text="missing")
    marker = "/seges/comprasgov/"
    if marker not in path or "/anual/" not in path:
        return httpx.Response(404, text="missing")
    rel = path.split(marker, 1)[1]
    target = planted / rel
    if not target.is_file():
        return httpx.Response(404, text="missing")
    return httpx.Response(200, content=target.read_bytes(), headers={"content-type": "text/csv"})


def _assert_planted_anual_partitions(settings: Settings) -> None:
    store = LandingStore(settings)
    year_keys = store.year_partition_keys("compras_gov")
    if not year_keys:
        raise SystemExit("FETCH=1 anual landing has no year= partitions")
    planted_ids = {
        2024: FETCH_ANUAL_2024,
        2025: FETCH_ANUAL_2025,
        2026: FETCH_ANUAL_2026,
    }
    for year, want in planted_ids.items():
        found = [k for k in year_keys if f"year={year}" in Path(k).parts]
        if not found:
            raise SystemExit(f"FETCH=1 anual dropped year={year} parquet")
        if not any("date=" in k for k in found):
            raise SystemExit(f"FETCH=1 anual year={year} is not also partitioned by date")
        ids: set[str] = set()
        for key in found:
            df = store.read_parquet(key)
            if "idcompra" not in df.columns:
                raise SystemExit(f"FETCH=1 anual year={year} parquet missing idcompra: {key}")
            ids.update(str(v) for v in df["idcompra"].to_list())
        if want not in ids:
            raise SystemExit(f"FETCH=1 anual year={year} lost planted {want}: {sorted(ids)}")
        leaked = [other for other_year, other in planted_ids.items() if other_year != year and other in ids]
        if leaked:
            raise SystemExit(f"FETCH=1 anual year={year} absorbed {leaked}")


def _assert_tier_a_landing(settings: Settings, ocds_report: dict) -> None:
    store = LandingStore(settings)
    for source in (
        "ocds",
        "receita_cnpj",
        "receita_cnpj_socios",
        "receita_cnpj_cnaes",
        "receita_cnpj_qualificacoes",
        "pncp_consulta",
    ):
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
            if source == "receita_cnpj":
                expected = load_adjacency_expected()
                landed = (
                    {"".join(c for c in str(v) if c.isalnum()).upper() for v in df["cnpj"].to_list()}
                    if "cnpj" in df.columns
                    else set()
                )
                need = {str(row["leftCnpj"]) for row in expected["edges"]}
                need |= {str(row["rightCnpj"]) for row in expected["edges"]}
                need |= {str(cnpj) for cnpj in expected["clean"]}
                missing = need - landed
                if missing:
                    raise SystemExit(f"receita landing missing planted adjacency CNPJs {sorted(missing)}")
            if source == "receita_cnpj_socios":
                if df.is_empty():
                    raise SystemExit("receita_cnpj_socios landed empty from fixture")
                if mask_cpf(RAW_CPF) not in " ".join(blobs):
                    raise SystemExit("receita socios missing masked CPF")
            if source == "receita_cnpj_cnaes":
                if df.is_empty():
                    raise SystemExit("receita_cnpj_cnaes landed empty from fixture")
                codes = {str(v) for v in df["codigo"].to_list()} if "codigo" in df.columns else set()
                if "4761001" not in codes:
                    raise SystemExit(f"receita cnaes missing 4761001: {codes}")
            if source == "receita_cnpj_qualificacoes":
                if df.is_empty():
                    raise SystemExit("receita_cnpj_qualificacoes landed empty from fixture")
            if source == "ocds" and df.is_empty():
                raise SystemExit("ocds landed empty from fixture")
            if source == "pncp_consulta":
                if df.is_empty():
                    raise SystemExit("pncp_consulta landed empty from fixture")
                ids = {str(v) for v in df["numero_controle_pncp"].to_list()} if "numero_controle_pncp" in df.columns else set()
                if PNCP_COMPRA_1 not in ids or PNCP_COMPRA_2 not in ids:
                    raise SystemExit(f"pncp_consulta fixture missing compras: {ids}")
                if PNCP_COMPRA_GAP not in ids:
                    raise SystemExit(f"pncp_consulta fixture missing planted gap: {ids}")
                if mask_cpf(RAW_CPF) not in " ".join(blobs):
                    raise SystemExit("pncp_consulta missing masked CPF")
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
    cnaes_first = store.list_parquet("receita_cnpj_cnaes")
    quals_first = store.list_parquet("receita_cnpj_qualificacoes")
    land_receita_cnpj(settings, store, cnpj_basicos=basicos)
    if len(store.list_parquet("receita_cnpj")) != len(receita_first):
        raise SystemExit("receita reland wrote a second parquet")
    if len(store.list_parquet("receita_cnpj_socios")) != len(socios_first):
        raise SystemExit("receita socios reland wrote a second parquet")
    if len(store.list_parquet("receita_cnpj_cnaes")) != len(cnaes_first):
        raise SystemExit("receita cnaes reland wrote a second parquet")
    if len(store.list_parquet("receita_cnpj_qualificacoes")) != len(quals_first):
        raise SystemExit("receita qualificacoes reland wrote a second parquet")
    pncp_first = store.list_parquet("pncp_consulta")
    land_pncp_consulta(settings, store)
    if len(store.list_parquet("pncp_consulta")) != len(pncp_first):
        raise SystemExit("pncp_consulta reland wrote a second parquet")
    tce_first = store.list_parquet(TCE_SP_SOURCE)
    land_tce_sp_licitacao(settings, store)
    if len(store.list_parquet(TCE_SP_SOURCE)) != len(tce_first):
        raise SystemExit("tce_sp_licitacao reland wrote a second parquet")
    tce_rs_first = store.list_parquet(TCE_RS_SOURCE)
    ref, _ = land_tce_rs_licitacon(settings, store)
    if ref.key not in tce_rs_first:
        raise SystemExit("tce_rs_licitacon reland produced a new content-hashed key")
    if len(store.list_parquet(TCE_RS_SOURCE)) != len(tce_rs_first):
        raise SystemExit("tce_rs_licitacon reland wrote a second parquet")
    cgu_first = store.list_parquet(CGU_SOURCE)
    ref, _ = land_cgu_ceis_cnep(settings, store)
    if ref.key not in cgu_first:
        raise SystemExit("cgu_ceis_cnep reland produced a new content-hashed key")
    if len(store.list_parquet(CGU_SOURCE)) != len(cgu_first):
        raise SystemExit("cgu_ceis_cnep reland wrote a second parquet")


class _RecordSleep:
    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(float(seconds))


def _fixture_official() -> PncpOfficial:
    return PncpOfficial(
        PNCP_CONSULTA_BASE,
        PNCP_CONSULTA_OPENAPI,
        PNCP_CONSULTA_SWAGGER,
        PNCP_API_BASE,
        PNCP_PUBLICACAO_PATH,
        PNCP_COMPRA_PATH,
        PNCP_ITENS_PATH,
        PNCP_ITEM_RESULTADOS_PATH,
        (8,),
    )


def _assert_pncp_spacing_and_resume(settings: Settings) -> None:
    if MIN_INTERVAL_S < 1.0:
        raise SystemExit("PNCP spacing constant is below 1s")
    try:
        RateLimiter(0.5)
    except ValueError:
        pass
    else:
        raise SystemExit("RateLimiter accepted spacing below 1s")
    if settings.pncp_consulta_dir is None:
        raise SystemExit("PNCP_CONSULTA_DIR fixture is missing")
    _assert_pncp_spacing(settings)
    _assert_pncp_resume(settings)
    _assert_pncp_gaps_planted(settings)


def _assert_pncp_spacing(settings: Settings) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="pncp-space-"))
    local = replace(settings, landing_uri=str(tmp))
    store = LandingStore(local)
    sleeper = _RecordSleep()
    transport = FixtureTransport(local.pncp_consulta_dir)
    land_pncp_consulta(
        local,
        store,
        official=_fixture_official(),
        transport=transport,
        sleeper=sleeper,
    )
    n = len(transport.calls)
    if n < 2:
        raise SystemExit("pncp fixture made too few HTTP calls to prove spacing")
    if len(sleeper.delays) < n - 1:
        raise SystemExit("PNCP spacing skipped")
    if any(d < 1.0 for d in sleeper.delays):
        raise SystemExit("PNCP spacing below 1s")


def _assert_pncp_resume(settings: Settings) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="pncp-resume-"))
    local = replace(settings, landing_uri=str(tmp))
    store = LandingStore(local)
    first = FixtureTransport(local.pncp_consulta_dir)
    interrupted = InterruptTransport(first, fail_on_publicacao_page=2)
    try:
        land_pncp_consulta(
            local,
            store,
            official=_fixture_official(),
            transport=interrupted,
            sleeper=_RecordSleep(),
        )
    except RuntimeError as exc:
        if "injected interrupt" not in str(exc):
            raise
    else:
        raise SystemExit("pncp resume test expected an interrupt after page 1")
    if not store.exists(CURSOR_KEY):
        raise SystemExit("pncp resume lost the cursor")
    cursor = json.loads(store.get(CURSOR_KEY).decode())
    if PNCP_COMPRA_1 not in {str(x) for x in cursor.get("completed_ids") or []}:
        raise SystemExit("pncp resume cursor lost the last successful id")
    if int(cursor.get("page") or 0) < 2:
        raise SystemExit(f"pncp resume cursor lost the next page: {cursor}")
    second = FixtureTransport(local.pncp_consulta_dir)
    ref, df, _ = land_pncp_consulta(
        local,
        store,
        official=_fixture_official(),
        transport=second,
        sleeper=_RecordSleep(),
    )
    if _fetched_sequencial(second.calls, 1):
        raise SystemExit("pncp resume re-fetched a completed compra")
    if not _fetched_sequencial(second.calls, 2):
        raise SystemExit("pncp resume did not continue to the next compra")
    ids = {str(v) for v in df["numero_controle_pncp"].to_list()} if "numero_controle_pncp" in df.columns else set()
    if PNCP_COMPRA_1 not in ids or PNCP_COMPRA_2 not in ids:
        raise SystemExit(f"pncp resume dropped rows: {ids}")
    if ref.source != "pncp_consulta" or "date=" not in ref.key:
        raise SystemExit(f"pncp resume landing is not hashed by source/date: {ref.key}")


def _assert_pncp_gaps_job(settings: Settings) -> None:
    from compras_ingest.assets import (
        GAPS_ASSET_NAME,
        GAPS_JOB_NAME,
        GAPS_SCHEDULE_CRON,
        GAPS_SCHEDULE_NAME,
        GAPS_SCHEDULE_TZ,
        defs,
    )

    if settings.pncp_consulta_fetch:
        raise SystemExit("fixture e2e must run with PNCP_CONSULTA_FETCH off")
    targets = live_ibge_targets()
    if len(targets) != 59:
        raise SystemExit(f"PNCP gaps live targets {len(targets)} != 59")
    ibges = {ibge for ibge, _ in targets}
    if ibges != set(SLICE_IBGE_CODES):
        raise SystemExit("PNCP gaps live targets drifted from the 59")
    pub = f"{PNCP_CONSULTA_BASE}{PNCP_PUBLICACAO_PATH}"
    compra = f"{PNCP_CONSULTA_BASE}{PNCP_COMPRA_PATH}"
    itens = f"{PNCP_API_BASE}{PNCP_ITENS_PATH}"
    resultados = f"{PNCP_API_BASE}{PNCP_ITEM_RESULTADOS_PATH}"
    for url in (pub, compra, itens, resultados):
        if "pncp.gov.br" not in url:
            raise SystemExit(f"PNCP URL is not official: {url}")
        if not url.startswith("https://pncp.gov.br/"):
            raise SystemExit(f"PNCP URL host shape is wrong: {url}")
    if pub != "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao":
        raise SystemExit(f"publicacao URL drifted: {pub}")
    if GAPS_SCHEDULE_TZ != "America/Sao_Paulo":
        raise SystemExit(f"PNCP gaps tz is {GAPS_SCHEDULE_TZ}")
    found = next((s for s in (defs.schedules or []) if s.name == GAPS_SCHEDULE_NAME), None)
    if found is None:
        raise SystemExit(f"defs missing schedule {GAPS_SCHEDULE_NAME}")
    if found.cron_schedule != GAPS_SCHEDULE_CRON:
        raise SystemExit(f"PNCP gaps cron {found.cron_schedule} != {GAPS_SCHEDULE_CRON}")
    if found.execution_timezone != GAPS_SCHEDULE_TZ:
        raise SystemExit(f"PNCP gaps tz is {found.execution_timezone}")
    target = found.job_name or getattr(found.job, "name", "")
    if target != GAPS_JOB_NAME:
        raise SystemExit(f"gaps schedule does not target {GAPS_JOB_NAME}: {target}")
    job = defs.resolve_job_def(GAPS_JOB_NAME)
    from compras_ingest.assets import _job_asset_keys

    selected = _job_asset_keys(job)
    if selected and GAPS_ASSET_NAME not in selected:
        raise SystemExit(f"{GAPS_JOB_NAME} missing {GAPS_ASSET_NAME}")


def _assert_pncp_gaps_planted(settings: Settings) -> None:
    if settings.pncp_consulta_dir is None:
        raise SystemExit("PNCP_CONSULTA_DIR fixture is missing")
    if settings.pncp_consulta_fetch:
        raise SystemExit("fixture e2e must not call resolve_pncp_consulta")
    tmp = Path(tempfile.mkdtemp(prefix="pncp-gaps-"))
    local = replace(settings, landing_uri=str(tmp))
    store = LandingStore(local)
    land_compras_gov(local, store)
    covered = complete_compra_keys(store)
    if not covered:
        raise SystemExit("planted gaps test has no compras.gov coverage")
    first = FixtureTransport(local.pncp_consulta_dir)
    ref, df, report = land_pncp_consulta_gaps(
        local,
        store,
        official=_fixture_official(),
        transport=first,
        sleeper=_RecordSleep(),
        covered=covered,
    )
    if report.get("mode") != "fixture":
        raise SystemExit(f"PNCP gaps fixture mode leaked fetch: {report}")
    if _fetched_sequencial(first.calls, 1):
        raise SystemExit("PNCP gaps re-fetched a complete compras.gov compra")
    if _fetched_sequencial(first.calls, 2):
        raise SystemExit("PNCP gaps re-fetched the second complete compra")
    if not _fetched_sequencial(first.calls, 99):
        raise SystemExit("PNCP gaps did not fetch the planted gap")
    if not any(PNCP_PUBLICACAO_PATH in url for url, _ in first.calls):
        raise SystemExit("PNCP gaps skipped publicacao discovery")
    for url, _query in first.calls:
        if "pncp.gov.br" not in url:
            raise SystemExit(f"PNCP gaps used a non-official URL: {url}")
        if not url.startswith(PNCP_CONSULTA_BASE) and not url.startswith(PNCP_API_BASE):
            raise SystemExit(f"PNCP gaps URL is not an official constant shape: {url}")
    ids = {str(v) for v in df["numero_controle_pncp"].to_list()} if "numero_controle_pncp" in df.columns else set()
    if PNCP_COMPRA_GAP not in ids:
        raise SystemExit(f"PNCP gaps landing missed the planted gap: {ids}")
    blobs = [str(v) for col in df.columns for v in df[col].to_list()]
    assert_no_raw_cpf(blobs)
    if not store.exists(GAPS_CURSOR_KEY):
        raise SystemExit("PNCP gaps lost the cursor")
    first_keys = set(store.list_parquet("pncp_consulta"))
    second = FixtureTransport(local.pncp_consulta_dir)
    ref2, _, _ = land_pncp_consulta_gaps(
        local,
        store,
        official=_fixture_official(),
        transport=second,
        sleeper=_RecordSleep(),
        covered=covered,
    )
    if _fetched_sequencial(second.calls, 1) or _fetched_sequencial(second.calls, 99):
        raise SystemExit("PNCP gaps second run re-fetched a completed or complete row")
    if len(store.list_parquet("pncp_consulta")) != len(first_keys):
        raise SystemExit("PNCP gaps second run wrote a second parquet")
    if ref2.sha256 != ref.sha256:
        raise SystemExit("PNCP gaps content hash moved with the same payload")


def _assert_pncp_gap_warehouse(settings: Settings) -> None:
    if fetch_contratacao(settings, PNCP_COMPRA_1) is not None:
        raise SystemExit("complete PNCP compra was written as a gap")
    gap = fetch_contratacao(settings, PNCP_COMPRA_GAP)
    if gap is None:
        raise SystemExit(f"warehouse missing planted PNCP gap {PNCP_COMPRA_GAP}")
    if str(gap.get("source") or "") != "pncp_consulta":
        raise SystemExit(f"PNCP gap source is not pncp_consulta: {gap.get('source')}")
    rows = fetch_items_for(settings, str(gap["id"]))
    if not rows:
        raise SystemExit("warehouse missing items for the planted PNCP gap")
    if not any(PNCP_GAP_DESC in str(row.get("descricao") or "") for row in rows):
        raise SystemExit("warehouse gap item is not the planted grampeador")


def _assert_tce_sp_host_refused() -> None:
    try:
        assert_official_host("https://example.com/licitacao-2024-01.zip", TCE_SP_HOSTS)
    except RuntimeError:
        pass
    else:
        raise SystemExit("TCE-SP allowlist accepted a non-official host")
    try:
        licitacao_zip_from_listing(
            '<a href="https://evil.example/licitacao-2024-01.zip">x</a>',
            2024,
            1,
            TCE_SP_LISTING_URL,
        )
    except RuntimeError as exc:
        if "refusing non-official host" not in str(exc):
            raise SystemExit(f"TCE-SP listing parser failed for the wrong reason: {exc}") from exc
    else:
        raise SystemExit("TCE-SP listing parser accepted a non-official host")


def _assert_tce_sp_landing(settings: Settings) -> None:
    if settings.tce_sp_path is None:
        raise SystemExit("TCE_SP_PATH fixture is missing")
    _assert_fixture_propostas_not_winner_only(settings)
    store = LandingStore(settings)
    keys = [k for k in store.list_parquet(TCE_SP_SOURCE) if k.endswith(".parquet")]
    if not keys:
        raise SystemExit("no tce_sp_licitacao parquet in landing")
    for key in keys:
        if "date=" not in key:
            raise SystemExit(f"tce_sp_licitacao not partitioned by date: {key}")
        digest = Path(key).stem
        if len(digest) != 64:
            raise SystemExit(f"tce_sp_licitacao key is not content-hashed sha256: {key}")
        df = store.read_parquet(key)
        if df.is_empty():
            raise SystemExit("tce_sp_licitacao landed empty from fixture")
        blobs = [str(v) for col in df.columns for v in df[col].to_list()]
        assert_no_raw_cpf(blobs)
        if mask_cpf(RAW_CPF) not in " ".join(blobs):
            raise SystemExit("tce_sp_licitacao missing masked CPF")
        if TCE_WINNER_CNPJ not in " ".join(blobs):
            raise SystemExit("tce_sp_licitacao dropped participant CNPJ")
        if TCE_OTHER_CNPJ in " ".join(blobs):
            raise SystemExit("tce_sp_licitacao landed a row outside the Bauru slice")
        mun_col = _require_col(df, "municipio")
        for value in df[mun_col].to_list():
            if fold(str(value or "")) != "bauru":
                raise SystemExit(f"tce_sp_licitacao landed non-Bauru município: {value}")
        _assert_propostas_not_winner_only(df, "tce_sp_licitacao landing")


def _assert_fixture_propostas_not_winner_only(settings: Settings) -> None:
    path = settings.tce_sp_path
    if path is None:
        raise SystemExit("TCE_SP_PATH fixture is missing")
    csv_path = path if path.is_file() else next(iter(sorted(path.glob("*.csv"))), None)
    if csv_path is None:
        raise SystemExit("TCE-SP fixture csv is missing")
    import csv

    import polars as pl

    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter=";")
        header = next(reader)
        rows = list(reader)
    raw = pl.DataFrame(rows, schema=header, orient="row")
    _assert_propostas_not_winner_only(raw, "tce_sp_licitacao fixture")


def _assert_propostas_not_winner_only(df, label: str) -> None:
    result_col = _require_col(df, "resultado da habilitacao")
    value_col = _require_col(df, "valor da proposta")
    loser_values = 0
    winner_values = 0
    for row in df.iter_rows(named=True):
        value = str(row.get(value_col) or "").strip()
        if not value:
            continue
        result = fold(str(row.get(result_col) or ""))
        if "vencedor" in result:
            winner_values += 1
        else:
            loser_values += 1
    if winner_values < 1:
        raise SystemExit(f"{label} has no winner Valor da Proposta")
    if loser_values < 1:
        raise SystemExit(f"Valor da Proposta is winner-only in {label}")
    joined = " ".join(str(v) for v in df[value_col].to_list())
    if TCE_LOSER_PROPOSTA not in joined:
        raise SystemExit(f"{label} missing loser Valor da Proposta {TCE_LOSER_PROPOSTA}")


def _assert_tce_sp_not_public(settings: Settings) -> None:
    blobs = fetch_explorer_text_blobs(settings)
    leaked = [token for token in (TCE_LOSER_CNPJ, TCE_WINNER_CNPJ, TCE_LOSER_PROPOSTA) if token in " ".join(blobs)]
    if leaked:
        raise SystemExit(f"TCE-SP participant proposal leaked into explorer tables: {leaked}")


def _assert_tce_rs_host_refused() -> None:
    try:
        assert_official_host("https://example.com/licitacoes-consolidado-2025.csv.zip", TCE_RS_HOSTS)
    except RuntimeError:
        pass
    else:
        raise SystemExit("TCE-RS allowlist accepted a non-official host")
    try:
        ckan_zip_from_package(
            {
                "result": {
                    "resources": [
                        {
                            "name": "licitacoes-consolidado-2025.csv.zip",
                            "url": "https://evil.example/licitacoes-consolidado-2025.csv.zip",
                        }
                    ]
                }
            },
            2025,
        )
    except RuntimeError as exc:
        if "refusing non-official host" not in str(exc):
            raise SystemExit(f"TCE-RS CKAN parser failed for the wrong reason: {exc}") from exc
    else:
        raise SystemExit("TCE-RS CKAN parser accepted a non-official host")


def _assert_tce_rs_landing(settings: Settings) -> None:
    if settings.tce_rs_path is None:
        raise SystemExit("TCE_RS_PATH fixture is missing")
    _assert_tce_rs_fixture_propostas_not_winner_only(settings)
    store = LandingStore(settings)
    keys = [k for k in store.list_parquet(TCE_RS_SOURCE) if k.endswith(".parquet")]
    if not keys:
        raise SystemExit("no tce_rs_licitacon parquet in landing")
    hashes = set()
    for key in keys:
        if "date=" not in key:
            raise SystemExit(f"tce_rs_licitacon not partitioned by date: {key}")
        digest = Path(key).stem
        if len(digest) != 64:
            raise SystemExit(f"tce_rs_licitacon key is not content-hashed sha256: {key}")
        hashes.add(digest)
        df = store.read_parquet(key)
        if df.is_empty():
            raise SystemExit("tce_rs_licitacon landed empty from fixture")
        blobs = [str(v) for col in df.columns for v in df[col].to_list()]
        joined = " ".join(blobs)
        assert_no_raw_cpf(blobs)
        if RAW_CPF in joined:
            raise SystemExit("tce_rs_licitacon stored a raw 11-digit CPF")
        if mask_cpf(RAW_CPF) not in joined:
            raise SystemExit("tce_rs_licitacon missing masked CPF")
        if TCE_RS_WINNER_CNPJ not in joined:
            raise SystemExit("tce_rs_licitacon dropped participant CNPJ")
        if TCE_RS_LOSER_CNPJ not in joined:
            raise SystemExit("tce_rs_licitacon dropped loser CNPJ")
        if TCE_RS_TABLE not in df.columns:
            raise SystemExit("tce_rs_licitacon missing _table")
        have = {str(v) for v in df[TCE_RS_TABLE].to_list()}
        missing = TCE_RS_TABLES - have
        if missing:
            raise SystemExit(f"tce_rs_licitacon missing tables {sorted(missing)}")
        _assert_tce_rs_propostas_not_winner_only(df, "tce_rs_licitacon landing")
    if len(hashes) != 1:
        raise SystemExit(f"tce_rs_licitacon hash is not stable: {hashes}")


def _assert_tce_rs_fixture_propostas_not_winner_only(settings: Settings) -> None:
    path = settings.tce_rs_path
    if path is None:
        raise SystemExit("TCE_RS_PATH fixture is missing")
    proposta = path if path.is_file() and "proposta" in path.name.lower() else next(iter(sorted(path.glob("PROPOSTA*"))), None)
    if proposta is None:
        raise SystemExit("TCE-RS fixture PROPOSTA is missing")
    text = proposta.read_text(encoding="utf-8")
    if TCE_RS_WINNER_CNPJ not in text or TCE_RS_LOSER_CNPJ not in text:
        raise SystemExit("TCE-RS fixture PROPOSTA is winner-only")
    if TCE_RS_LOSER_PROPOSTA not in text:
        raise SystemExit(f"TCE-RS fixture missing loser VL_TOTAL_PROPOSTA {TCE_RS_LOSER_PROPOSTA}")
    if "|D|" not in text or "|C|" not in text:
        raise SystemExit("TCE-RS fixture PROPOSTA missing C and D results")


def _assert_tce_rs_propostas_not_winner_only(df, label: str) -> None:
    if TCE_RS_TABLE not in df.columns:
        raise SystemExit(f"{label} missing {TCE_RS_TABLE}")
    rows = [r for r in df.iter_rows(named=True) if str(r.get(TCE_RS_TABLE) or "") == "PROPOSTA"]
    if not rows:
        raise SystemExit(f"{label} has no PROPOSTA rows")
    result_col = _require_col(df, "tp_resultado_proposta")
    value_col = _require_col(df, "vl_total_proposta")
    winners = 0
    losers = 0
    for row in rows:
        value = str(row.get(value_col) or "").strip()
        if not value:
            continue
        result = fold(str(row.get(result_col) or ""))
        if result == "c":
            winners += 1
        elif result == "d":
            losers += 1
    if winners < 1:
        raise SystemExit(f"{label} has no classificado VL_TOTAL_PROPOSTA")
    if losers < 1:
        raise SystemExit(f"VL_TOTAL_PROPOSTA is winner-only in {label}")
    joined = " ".join(str(row.get(value_col) or "") for row in rows)
    if TCE_RS_LOSER_PROPOSTA not in joined:
        raise SystemExit(f"{label} missing loser VL_TOTAL_PROPOSTA {TCE_RS_LOSER_PROPOSTA}")


def _assert_tce_rs_not_public(settings: Settings) -> None:
    blobs = fetch_explorer_text_blobs(settings)
    leaked = [
        token
        for token in (TCE_RS_LOSER_CNPJ, TCE_RS_WINNER_CNPJ, TCE_RS_LOSER_PROPOSTA)
        if token in " ".join(blobs)
    ]
    if leaked:
        raise SystemExit(f"TCE-RS participant proposal leaked into explorer tables: {leaked}")


def _assert_cgu_host_refused() -> None:
    try:
        assert_official_host("https://evil.example/20240315_CEIS.zip", CGU_HOSTS)
    except RuntimeError:
        pass
    else:
        raise SystemExit("CGU allowlist accepted a non-official host")
    try:
        assert_cgu_zip_url("https://evil.example/PortalDaTransparencia/saida/ceis/20240315_CEIS.zip", "ceis")
    except RuntimeError as exc:
        if "refusing non-official host" not in str(exc) and "not official" not in str(exc):
            raise SystemExit(f"CGU zip parser failed for the wrong reason: {exc}") from exc
    else:
        raise SystemExit("CGU zip parser accepted a non-official host")


def _assert_cgu_ceis_cnep_landing(settings: Settings) -> None:
    if settings.sanctions_dir is None:
        raise SystemExit("SANCTIONS_DIR fixture is missing")
    if settings.sanctions_fetch:
        raise SystemExit("fixture mode resolved a live CGU fetch")
    store = LandingStore(settings)
    keys = [k for k in store.list_parquet(CGU_SOURCE) if k.endswith(".parquet")]
    if not keys:
        raise SystemExit("no cgu_ceis_cnep parquet in landing")
    hashes = set()
    cadastros = set()
    for key in keys:
        if "date=" not in key:
            raise SystemExit(f"cgu_ceis_cnep not partitioned by date: {key}")
        digest = Path(key).stem
        if len(digest) != 64:
            raise SystemExit(f"cgu_ceis_cnep key is not content-hashed sha256: {key}")
        hashes.add(digest)
        df = store.read_parquet(key)
        if df.is_empty():
            raise SystemExit("cgu_ceis_cnep landed empty from fixture")
        blobs = [str(v) for col in df.columns for v in df[col].to_list()]
        joined = " ".join(blobs)
        assert_no_raw_cpf(blobs)
        if RAW_CPF in joined:
            raise SystemExit("cgu_ceis_cnep stored a raw 11-digit CPF")
        if mask_cpf(RAW_CPF) not in joined:
            raise SystemExit("cgu_ceis_cnep missing masked CPF")
        cad_col = _require_col(df, "cadastro")
        cadastros |= {fold(str(v)) for v in df[cad_col].to_list()}
        for token in (SANCTION_CNPJ_A, SANCTION_CNPJ_CNEP, SANCTION_CNPJ_B, SANCTION_CNPJ_C, SANCTION_CNPJ_D):
            if token not in joined:
                raise SystemExit(f"cgu_ceis_cnep dropped planted CNPJ {token}")
        if SANCTION_CNPJ_E in joined:
            raise SystemExit("cgu_ceis_cnep planted a clean CNPJ as sanctioned")
    if "ceis" not in cadastros or "cnep" not in cadastros:
        raise SystemExit(f"cgu_ceis_cnep missing CEIS or CNEP cadastro: {sorted(cadastros)}")
    if len(hashes) != 1:
        raise SystemExit(f"cgu_ceis_cnep hash is not stable: {hashes}")
    for key in keys:
        meta_key = key[: -len(".parquet")] + ".source.json"
        if not store.exists(meta_key):
            raise SystemExit(f"cgu_ceis_cnep missing source.json for {key}")
        meta = json.loads(store.get(meta_key).decode())
        if meta.get("mode") != "fixture":
            raise SystemExit(f"cgu_ceis_cnep fixture landing mode is not fixture: {meta}")
        if meta.get("public") is not False or meta.get("explorer") is not False:
            raise SystemExit("cgu_ceis_cnep landing is not internal")


def _assert_sanction_flags(items, flags, stored) -> None:
    planted = _flagged_cnpjs(items, flags)
    if planted != set(SANCTION_OVERLAP):
        raise SystemExit(f"sanction flags CNPJs {sorted(planted)} != planted overlap {sorted(SANCTION_OVERLAP)}")
    leaked = planted & set(SANCTION_CLEAN)
    if leaked:
        raise SystemExit(f"sanction flags included non-overlap CNPJs {sorted(leaked)}")
    deltas = [str(row.get("delta") or "") for row in flags.iter_rows(named=True) if str(row.get("kind") or "") == "sanctioned_ceis_cnep"]
    if not any("CEIS" in delta for delta in deltas):
        raise SystemExit("sanction flags missed the CEIS cadastro")
    if not any("CNEP" in delta for delta in deltas):
        raise SystemExit("sanction flags missed the CNEP cadastro")
    kinds = {str(row["kind"]) for row in stored}
    if "sanctioned_ceis_cnep" not in kinds:
        raise SystemExit("warehouse missing sanctioned_ceis_cnep after write_flags")
    if AGE_FLAG_KIND not in kinds:
        raise SystemExit("warehouse missing cnpj_age after write_flags")
    if AGE_INFO_KIND not in kinds:
        raise SystemExit("warehouse missing cnpj_age_info after write_flags")
    id_to_cnpj = {}
    for row in items.iter_rows(named=True):
        iid = item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or ""))
        digits = "".join(c for c in str(row.get("fornecedor_cnpj") or "") if c.isdigit())
        id_to_cnpj[iid] = digits
    ware = set()
    for row in stored:
        if str(row.get("kind") or "") != "sanctioned_ceis_cnep":
            continue
        if str(row.get("state") or "") != "detected":
            raise SystemExit(f"sanctioned_ceis_cnep state is not detected: {row.get('state')}")
        cnpj = id_to_cnpj.get(str(row.get("itemId") or ""))
        if cnpj:
            ware.add(cnpj)
    if ware != set(SANCTION_OVERLAP):
        raise SystemExit(f"warehouse sanction CNPJs {sorted(ware)} != planted overlap {sorted(SANCTION_OVERLAP)}")
    if ware & set(SANCTION_CLEAN):
        raise SystemExit(f"warehouse flagged non-overlap CNPJs {sorted(ware & set(SANCTION_CLEAN))}")


def _frac_amounts():
    table = load_thresholds()
    t24 = table[(2024, "compras")].amount
    t25 = table[(2025, "compras")].amount
    q = Decimal("0.01")
    return {
        "over": (t24 * Decimal(2) / Decimal(5)).quantize(q),
        "cluster": (t24 * Decimal(91) / Decimal(100)).quantize(q),
        "big": t24,
        "small": (t24 / Decimal(10)).quantize(q),
        "other_year": ((t24 + t25) / Decimal(4)).quantize(q),
        "t24": t24,
        "t25": t25,
    }


def _load_cnae_mismatch_expected() -> dict:
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "detect" / "fixtures" / "cnae_mismatch" / "expected.json"
        if cand.is_file():
            return json.loads(cand.read_text(encoding="utf-8"))
    raise SystemExit("cnae_mismatch expected.json missing")


def _assert_cnae_allowlist() -> None:
    from urllib.parse import urlparse

    table = load_allowlist()
    if "8920" not in table or "7510" not in table:
        raise SystemExit(f"cnae allow-list missing planted classes: {sorted(table)}")
    if "9999" in table:
        raise SystemExit("unmapped plant class 9999 is in the allow-list")
    text = Path(CNAE_ALLOW_PATH).read_text(encoding="utf-8")
    for url in ("https://catalogo.compras.gov.br/", "https://concla.ibge.gov.br/busca-online-cnae.html"):
        if url not in text:
            raise SystemExit(f"cnae allow-list missing official url {url}")
        host = (urlparse(url).hostname or "").lower()
        if not any(host == h or host.endswith("." + h) for h in CNAE_OFFICIAL_HOSTS):
            raise SystemExit(f"cnae allow-list url host is not official: {url}")
    detect_root = Path(CNAE_ALLOW_PATH).resolve().parents[1]
    for path in detect_root.rglob("*.py"):
        blob = path.read_text(encoding="utf-8")
        if "http://" in blob or "https://" in blob:
            if "compras.gov.br" not in blob and "concla.ibge.gov.br" not in blob and "gov.br" not in blob:
                raise SystemExit(f"detector python has unofficial url: {path}")


def _assert_cnae_mismatch_flags(items, flags, stored) -> None:
    expected = _load_cnae_mismatch_expected()
    want = set(expected["flag"])
    absent = set(expected["absent"])
    if want != set(CNAE_HIT_IDS) or absent != set(CNAE_CLEAN_IDS):
        raise SystemExit("cnae_mismatch expected.json drifted from planted ids")
    planted = want | absent
    if len(planted) != 9:
        raise SystemExit(f"cnae_mismatch planted coverage denominator {len(planted)} != 9")
    by_rec = {str(row.get("record_id") or ""): row for row in items.iter_rows(named=True)}
    missing_items = planted - set(by_rec)
    if missing_items:
        raise SystemExit(f"cnae_mismatch plants missing from normalized items: {sorted(missing_items)}")
    if str(by_rec["I-2024-B5-HIT-FOOD"].get("cnae") or "")[:2] not in {"64", "65", "66"}:
        raise SystemExit("HIT food plant is not finance CNAE 64/65/66")
    if str(by_rec["I-2024-B5-HIT-HOME"].get("cnae") or "")[:2] not in {"97", "98"}:
        raise SystemExit("HIT home plant is not domestic CNAE 97/98")
    if str(by_rec["I-2024-B5-CLEAN-PRI"].get("cnae") or "")[:2] != "10":
        raise SystemExit("CLEAN primary plant is not food CNAE 10")
    if "1061901" not in str(by_rec["I-2024-B5-CLEAN-SEC"].get("cnae_secundaria") or ""):
        raise SystemExit("CLEAN secondary plant missing saving CNAE")
    if str(by_rec["I-2024-B5-CLEAN-NOCNAE"].get("cnae") or "").strip():
        raise SystemExit("CLEAN missing CNAE plant has a CNAE")
    if str(by_rec["I-2024-B5-CLEAN-NOCAT"].get("catmat") or "").strip():
        raise SystemExit("CLEAN missing CATMAT plant has catmat")
    if str(by_rec["I-2024-B5-CLEAN-SERV"].get("material_ou_servico") or "").upper()[:1] != "S":
        raise SystemExit("CLEAN service plant is not tipo S")

    got: set[str] = set()
    for row in flags.iter_rows(named=True):
        if str(row.get("kind") or "") != CNAE_KIND:
            continue
        rid = str(row.get("record_id") or "")
        delta = str(row.get("delta") or "")
        for token in CNAE_DELTA_TOKENS:
            if token not in delta:
                raise SystemExit(f"{rid} cnae_mismatch delta missing {token}: {delta}")
        if CNAE_BANNED_DELTA.search(delta):
            raise SystemExit(f"{rid} cnae_mismatch delta is accusatory: {delta}")
        got.add(rid)
    extra = got - want
    missing = want - got
    leaked = got & absent
    if extra or missing or leaked:
        raise SystemExit(
            f"cnae_mismatch record_ids extra={sorted(extra)} missing={sorted(missing)} leaked={sorted(leaked)}"
        )
    if got != want:
        raise SystemExit(f"cnae_mismatch record_ids {sorted(got)} != planted hits {sorted(want)}")

    id_to_rid = {
        item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or "")): str(row.get("record_id") or "")
        for row in items.iter_rows(named=True)
    }
    ware: set[str] = set()
    for row in stored:
        if str(row.get("kind") or "") != CNAE_KIND:
            continue
        if str(row.get("state") or "") != "detected":
            raise SystemExit(f"cnae_mismatch state is not detected: {row.get('state')}")
        if row.get("publishedAt") not in (None, ""):
            raise SystemExit(f"cnae_mismatch publishedAt is set: {row.get('publishedAt')}")
        rid = id_to_rid.get(str(row.get("itemId") or ""))
        if not rid:
            raise SystemExit(f"cnae_mismatch itemId not in slice: {row.get('itemId')}")
        ware.add(rid)
    if ware != want:
        raise SystemExit(f"warehouse cnae_mismatch ids {sorted(ware)} != planted hits {sorted(want)}")
    if ware & absent:
        raise SystemExit(f"warehouse flagged a silent cnae_mismatch plant {sorted(ware & absent)}")


def _assert_fracionamento_table() -> None:
    from urllib.parse import urlparse

    table = load_thresholds()
    years = {year for year, _kind in table}
    if 2024 not in years or 2025 not in years:
        raise SystemExit(f"threshold table missing 2024 or 2025: {sorted(years)}")
    money = set()
    for row in table.values():
        host = (urlparse(row.url).hostname or "").lower()
        if not any(host == h or host.endswith("." + h) for h in FRAC_OFFICIAL_HOSTS):
            raise SystemExit(f"threshold url host is not official: {row.url}")
        money.add(str(row.amount))
        money.add(str(row.amount).split(".")[0])
    detect_root = Path(THRESH_PATH).resolve().parents[1]
    hits = []
    for path in detect_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in sorted(money, key=len, reverse=True):
            if len(token) < 4:
                continue
            if token in text:
                hits.append(f"{path.name}:{token}")
    if hits:
        raise SystemExit(f"detector python contains threshold money literals: {hits}")


def _assert_fracionamento_flags(items, flags, stored) -> None:
    want = _frac_amounts()
    by_rec = {}
    for row in items.iter_rows(named=True):
        rid = str(row.get("record_id") or "")
        by_rec[rid] = row
    planted = FRAC_OVER_IDS | FRAC_CLUSTER_IDS | FRAC_SILENT_IDS
    for rid in planted:
        if rid not in by_rec:
            raise SystemExit(f"fracionamento fixture missing normalized item {rid}")
    for rid in FRAC_OVER_IDS:
        got = parse_decimal(by_rec[rid].get("valor_total"))
        if got != want["over"]:
            raise SystemExit(f"{rid} amount {got} != table-derived over {want['over']}")
    for rid in FRAC_CLUSTER_IDS:
        got = parse_decimal(by_rec[rid].get("valor_total"))
        if got != want["cluster"]:
            raise SystemExit(f"{rid} amount {got} != table-derived cluster {want['cluster']}")
    if parse_decimal(by_rec["I-2024-B3-BIG-1"].get("valor_total")) != want["big"]:
        raise SystemExit("BIG-1 amount is not the loaded 2024 compras threshold")
    if parse_decimal(by_rec["I-2024-B3-BIG-2"].get("valor_total")) != want["small"]:
        raise SystemExit("BIG-2 amount is not table-derived small")
    if parse_decimal(by_rec["I-2024-B3-OTHERCLS"].get("valor_total")) != want["small"]:
        raise SystemExit("OTHERCLS amount is not table-derived small")
    for rid in ("I-2024-B3-PREGAO-1", "I-2024-B3-PREGAO-2", "I-2024-B3-PREGAO-3"):
        if parse_decimal(by_rec[rid].get("valor_total")) != want["over"]:
            raise SystemExit(f"{rid} amount is not the same table-derived over amount")
    year_sum = Decimal("0")
    for rid in ("I-2025-B3-OTHERYR-1", "I-2025-B3-OTHERYR-2"):
        got = parse_decimal(by_rec[rid].get("valor_total"))
        if got != want["other_year"]:
            raise SystemExit(f"{rid} amount {got} != table-derived other-year {want['other_year']}")
        year_sum += got
    if year_sum <= want["t24"] or year_sum >= want["t25"]:
        raise SystemExit(f"OTHER YEAR sum {year_sum} does not sit between 2024 and 2025 thresholds")

    got_over: set[str] = set()
    got_cluster: set[str] = set()
    for row in flags.iter_rows(named=True):
        kind = str(row.get("kind") or "")
        if kind not in FRAC_KINDS:
            continue
        rid = str(row.get("record_id") or "")
        delta = str(row.get("delta") or "")
        for token in FRAC_DELTA_TOKENS:
            if token not in delta:
                raise SystemExit(f"{rid} {kind} delta missing {token}: {delta}")
        if "class_key=codigo_classe:" not in delta:
            raise SystemExit(f"{rid} {kind} delta missing class_key=codigo_classe: {delta}")
        if kind == FRAC_CLUSTER_KIND:
            if "rule=cluster" not in delta:
                raise SystemExit(f"{rid} cluster delta missing rule=cluster: {delta}")
            got_cluster.add(rid)
        else:
            if "rule=over_sum" not in delta:
                raise SystemExit(f"{rid} over delta missing rule=over_sum: {delta}")
            got_over.add(rid)
    if got_over != set(FRAC_OVER_IDS):
        raise SystemExit(f"fracionamento record_ids {sorted(got_over)} != planted over {sorted(FRAC_OVER_IDS)}")
    if got_cluster != set(FRAC_CLUSTER_IDS):
        raise SystemExit(
            f"fracionamento_cluster record_ids {sorted(got_cluster)} != planted cluster {sorted(FRAC_CLUSTER_IDS)}"
        )
    leaked = (got_over | got_cluster) & set(FRAC_SILENT_IDS)
    if leaked:
        raise SystemExit(f"fracionamento flagged silent plants {sorted(leaked)}")
    extra = (got_over | got_cluster) - set(FRAC_OVER_IDS | FRAC_CLUSTER_IDS)
    if extra:
        raise SystemExit(f"fracionamento flagged unexpected records {sorted(extra)}")

    id_to_rid = {
        item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or "")): str(row.get("record_id") or "")
        for row in items.iter_rows(named=True)
    }
    ware_over: set[str] = set()
    ware_cluster: set[str] = set()
    for row in stored:
        kind = str(row.get("kind") or "")
        if kind not in FRAC_KINDS:
            continue
        if str(row.get("state") or "") != "detected":
            raise SystemExit(f"{kind} state is not detected: {row.get('state')}")
        if row.get("publishedAt") not in (None, ""):
            raise SystemExit(f"{kind} publishedAt is set: {row.get('publishedAt')}")
        rid = id_to_rid.get(str(row.get("itemId") or ""))
        if not rid:
            raise SystemExit(f"{kind} itemId not in slice: {row.get('itemId')}")
        delta = str(row.get("delta") or "")
        for token in FRAC_DELTA_TOKENS:
            if token not in delta:
                raise SystemExit(f"warehouse {rid} {kind} delta missing {token}: {delta}")
        if kind == FRAC_CLUSTER_KIND:
            ware_cluster.add(rid)
        else:
            ware_over.add(rid)
    if ware_over != set(FRAC_OVER_IDS):
        raise SystemExit(f"warehouse fracionamento ids {sorted(ware_over)} != planted over {sorted(FRAC_OVER_IDS)}")
    if ware_cluster != set(FRAC_CLUSTER_IDS):
        raise SystemExit(
            f"warehouse cluster ids {sorted(ware_cluster)} != planted cluster {sorted(FRAC_CLUSTER_IDS)}"
        )
    if (ware_over | ware_cluster) & set(FRAC_SILENT_IDS):
        raise SystemExit("warehouse flagged a silent fracionamento plant")
    stored_kinds = {str(row["kind"]) for row in stored}
    if FRAC_OVER_KIND not in stored_kinds:
        raise SystemExit("warehouse missing fracionamento after write_flags")
    if FRAC_CLUSTER_KIND not in stored_kinds:
        raise SystemExit("warehouse missing fracionamento_cluster after write_flags")


def _assert_cnpj_age_flags(items, flags, stored) -> None:
    by_rec = {}
    for row in items.iter_rows(named=True):
        rid = str(row.get("record_id") or "")
        digits = "".join(c for c in str(row.get("fornecedor_cnpj") or "") if c.isdigit())
        by_rec[rid] = {
            "cnpj": digits,
            "opened_on": str(row.get("opened_on") or ""),
            "award_date": str(row.get("award_date") or ""),
        }
    for rid in AGE_YOUNG_IDS | AGE_INFO_IDS | AGE_SILENT_IDS:
        if rid not in by_rec:
            raise SystemExit(f"cnpj_age fixture missing normalized item {rid}")
    if by_rec["I-2024-000001"]["cnpj"] != AGE_YOUNG_CNPJ:
        raise SystemExit(f"young plant CNPJ drifted: {by_rec['I-2024-000001']['cnpj']}")
    if by_rec["I-2024-B2-INFO"]["cnpj"] != AGE_INFO_CNPJ:
        raise SystemExit(f"info plant CNPJ drifted: {by_rec['I-2024-B2-INFO']['cnpj']}")
    if by_rec["I-2024-000002"]["cnpj"] != AGE_OLD_CNPJ:
        raise SystemExit(f"old plant CNPJ drifted: {by_rec['I-2024-000002']['cnpj']}")
    if by_rec["I-2024-B2-FUTURE"]["cnpj"] != AGE_FUTURE_CNPJ:
        raise SystemExit(f"future plant CNPJ drifted: {by_rec['I-2024-B2-FUTURE']['cnpj']}")
    if by_rec["I-2024-B2-NOOPEN"]["cnpj"] != AGE_NOOPEN_CNPJ:
        raise SystemExit(f"missing opened_on plant CNPJ drifted: {by_rec['I-2024-B2-NOOPEN']['cnpj']}")
    if by_rec["I-2024-B2-NOAWARD"]["cnpj"] != AGE_NODATE_CNPJ:
        raise SystemExit(f"missing award plant CNPJ drifted: {by_rec['I-2024-B2-NOAWARD']['cnpj']}")
    if by_rec["I-2024-B2-NOOPEN"]["opened_on"]:
        raise SystemExit("missing opened_on plant has opened_on")
    if by_rec["I-2024-B2-NOAWARD"]["award_date"]:
        raise SystemExit("missing award plant has award_date")

    got_flag: set[str] = set()
    got_info: set[str] = set()
    for row in flags.iter_rows(named=True):
        kind = str(row.get("kind") or "")
        rid = str(row.get("record_id") or "")
        if kind not in {AGE_FLAG_KIND, AGE_INFO_KIND}:
            continue
        delta = str(row.get("delta") or "")
        for token in ("opened_on=", "award_date=", "age_days=", "tier="):
            if token not in delta:
                raise SystemExit(f"{rid} {kind} delta missing {token}: {delta}")
        if kind == AGE_FLAG_KIND:
            if "tier=flag" not in delta:
                raise SystemExit(f"{rid} cnpj_age delta missing tier=flag: {delta}")
            if "tier=info" in delta:
                raise SystemExit(f"{rid} cnpj_age delta has tier=info: {delta}")
            got_flag.add(rid)
        else:
            if "tier=info" not in delta:
                raise SystemExit(f"{rid} cnpj_age_info delta missing tier=info: {delta}")
            if "tier=flag" in delta:
                raise SystemExit(f"{rid} cnpj_age_info delta has tier=flag: {delta}")
            got_info.add(rid)
    if got_flag != set(AGE_YOUNG_IDS):
        raise SystemExit(f"cnpj_age record_ids {sorted(got_flag)} != planted young {sorted(AGE_YOUNG_IDS)}")
    if got_info != set(AGE_INFO_IDS):
        raise SystemExit(f"cnpj_age_info record_ids {sorted(got_info)} != planted info {sorted(AGE_INFO_IDS)}")
    leaked = (got_flag | got_info) & set(AGE_SILENT_IDS)
    if leaked:
        raise SystemExit(f"cnpj_age flagged silent plants {sorted(leaked)}")
    if AGE_INFO_CNPJ in {by_rec[rid]["cnpj"] for rid in got_flag}:
        raise SystemExit("info plant was also kind=cnpj_age")
    if any(by_rec[rid]["cnpj"] == AGE_OLD_CNPJ for rid in got_flag | got_info):
        raise SystemExit("old plant was flagged")
    if any(by_rec[rid]["cnpj"] == AGE_FUTURE_CNPJ for rid in got_flag | got_info):
        raise SystemExit("future plant was flagged")

    id_to_rid = {
        item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or "")): str(row.get("record_id") or "")
        for row in items.iter_rows(named=True)
    }
    ware_flag: set[str] = set()
    ware_info: set[str] = set()
    for row in stored:
        kind = str(row.get("kind") or "")
        if kind not in {AGE_FLAG_KIND, AGE_INFO_KIND}:
            continue
        if str(row.get("state") or "") != "detected":
            raise SystemExit(f"{kind} state is not detected: {row.get('state')}")
        if row.get("publishedAt") not in (None, ""):
            raise SystemExit(f"{kind} publishedAt is set: {row.get('publishedAt')}")
        rid = id_to_rid.get(str(row.get("itemId") or ""))
        if not rid:
            raise SystemExit(f"{kind} itemId not in slice: {row.get('itemId')}")
        delta = str(row.get("delta") or "")
        for token in ("opened_on=", "award_date=", "age_days=", "tier="):
            if token not in delta:
                raise SystemExit(f"warehouse {rid} {kind} delta missing {token}: {delta}")
        if kind == AGE_FLAG_KIND:
            ware_flag.add(rid)
        else:
            ware_info.add(rid)
    if ware_flag != set(AGE_YOUNG_IDS):
        raise SystemExit(f"warehouse cnpj_age ids {sorted(ware_flag)} != planted young {sorted(AGE_YOUNG_IDS)}")
    if ware_info != set(AGE_INFO_IDS):
        raise SystemExit(f"warehouse cnpj_age_info ids {sorted(ware_info)} != planted info {sorted(AGE_INFO_IDS)}")
    if ware_flag & set(AGE_SILENT_IDS) or ware_info & set(AGE_SILENT_IDS):
        raise SystemExit("warehouse flagged a silent cnpj_age plant")


def _flagged_cnpjs(items, flags) -> set[str]:
    by_rec = {}
    for row in items.iter_rows(named=True):
        digits = "".join(c for c in str(row.get("fornecedor_cnpj") or "") if c.isdigit())
        by_rec[str(row.get("record_id") or "")] = digits
    out: set[str] = set()
    for row in flags.iter_rows(named=True):
        if str(row.get("kind") or "") != "sanctioned_ceis_cnep":
            continue
        cnpj = by_rec.get(str(row.get("record_id") or ""))
        if cnpj:
            out.add(cnpj)
    return out


def _require_col(df, needle: str) -> str:
    want = fold(needle)
    for col in df.columns:
        if fold(col) == want:
            return col
    raise SystemExit(f"missing column {needle}: {list(df.columns)}")


def _fetched_sequencial(calls: list[tuple[str, dict]], sequencial: int) -> bool:
    token = f"/compras/2024/{sequencial}"
    return any(token in url and "/itens" in url for url, _ in calls)


if __name__ == "__main__":
    sys.exit(main())
