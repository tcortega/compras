from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import httpx

from compras_detect.tier1 import run_tier1
from compras_ingest.cpf import assert_no_raw_cpf, mask_cpf
from compras_ingest.landing import LandingStore
from compras_ingest.official import (
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
    assert_official_host,
    ckan_zip_from_package,
    licitacao_zip_from_listing,
    resolve_ocds_feed,
    resolve_pncp_consulta,
    resolve_receita_index,
    resolve_tce_rs_licitacon,
    resolve_tce_sp_licitacao,
    tce_rs_ckan_url,
    tce_rs_portal_url,
)
from compras_ingest.pipeline import _collect_landing_records, land_second_snapshot, run_compras_slice
from compras_ingest.settings import Settings
from compras_ingest.sources.ocds import land_ocds
from compras_ingest.sources.pncp_consulta import (
    CURSOR_KEY,
    MIN_INTERVAL_S,
    FixtureTransport,
    InterruptTransport,
    RateLimiter,
    land_pncp_consulta,
)
from compras_ingest.sources.receita_cnpj import cnpj_basicos_from_frame, land_receita_cnpj
from compras_ingest.sources.tce_rs_licitacon import SOURCE as TCE_RS_SOURCE
from compras_ingest.sources.tce_rs_licitacon import TABLE_COL as TCE_RS_TABLE
from compras_ingest.sources.tce_rs_licitacon import land_tce_rs_licitacon
from compras_ingest.sources.tce_sp_licitacao import SOURCE as TCE_SP_SOURCE
from compras_ingest.sources.tce_sp_licitacao import land_tce_sp_licitacao
from compras_ingest.warehouse import (
    fact_columns,
    fetch_all_items,
    fetch_contratacao,
    fetch_flags,
    fetch_item_facts,
    fetch_items_for,
    fetch_one_orgao,
    fetch_raw_text_blobs,
    item_columns,
    write_flags,
)
from decimal import Decimal

from compras_normalize.text import fold, parse_decimal


ORGAO_CNPJ = "29477000000180"
PNCP_ID = "29477000000180-1-2024-000001"
RAW_CPF = "12345678901"
LANDED_SOURCES = (
    "compras_gov",
    "ocds",
    "receita_cnpj",
    "receita_cnpj_socios",
    "pncp_consulta",
    TCE_SP_SOURCE,
    TCE_RS_SOURCE,
)
TCE_WINNER_CNPJ = "34.914.897/0001-80"
TCE_LOSER_CNPJ = "11.021.249/0001-08"
TCE_OTHER_CNPJ = "00.000.000/0001-91"
TCE_LOSER_PROPOSTA = "32250,0"
TCE_RS_WINNER_CNPJ = "03722885000120"
TCE_RS_LOSER_CNPJ = "91549055000100"
TCE_RS_LOSER_PROPOSTA = "5493164,86"
TCE_RS_TABLES = {
    "LICITANTE",
    "PROPOSTA",
    "LOTE_PROPOSTA",
    "ITEM_PROPOSTA",
    "LICITACAO",
    "LOTE",
    "ITEM",
}
PNCP_COMPRA_1 = "29477000000180-1-000001/2024"
PNCP_COMPRA_2 = "29477000000180-1-000002/2024"
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
)


def main() -> int:
    settings = Settings.from_env()
    _check_defs()
    official = _assert_official_urls(settings)
    with _official_hosts_blocked():
        _assert_pncp_spacing_and_resume(settings)
        result = run_compras_slice(settings)
        _assert_landing(settings, result.landing.sha256)
        _assert_tier_a_landing(settings, result.ocds_report)
        _assert_tce_sp_landing(settings)
        _assert_tce_rs_landing(settings)
        _assert_write_once(settings)
    _assert_tce_sp_not_public(settings)
    _assert_tce_rs_not_public(settings)
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
    _assert_units(settings, result.items)
    store = LandingStore(settings)
    mutate = str(result.items["record_id"][0])
    land_second_snapshot(settings, mutate, store)
    landing_records = _collect_landing_records(store, "compras_gov")
    flags = run_tier1(result.items, landing_records=landing_records, sanctions=None)
    write_flags(settings, flags, result.items)
    stored = fetch_flags(settings, state="detected")
    kinds = {str(row["kind"]) for row in stored}
    if "qty_unit_price_neq_total" not in kinds:
        raise SystemExit("warehouse missing qty_unit_price_neq_total after write_flags")
    if "retroactive_edit" not in kinds:
        raise SystemExit("warehouse missing retroactive_edit after second landing")
    for row in stored:
        if not row.get("itemId"):
            raise SystemExit("warehouse flag missing itemId")
        if not row.get("delta"):
            raise SystemExit("warehouse flag missing delta")
        if not row.get("snapshotId"):
            raise SystemExit("warehouse flag missing snapshotId")
        if not row.get("methodologyVersion"):
            raise SystemExit("warehouse flag missing methodologyVersion")
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
    print(f"orgao={orgao['cnpj']} contratacao={contratacao['pncpId']} items={len(items)}")
    print(f"flags={sorted(kinds)}")
    return 0


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
        httpx.Client = self._client
        if exc_type is RuntimeError and exc and "fixture mode hit official host" in str(exc):
            raise SystemExit(str(exc)) from exc
        return False


def _fail_if_official_host(url) -> None:
    host = httpx.URL(str(url)).host or ""
    if host in OFFICIAL_HOSTS:
        raise RuntimeError(f"fixture mode hit official host {host}")


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
    try:
        pncp = resolve_pncp_consulta()
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
        tce = resolve_tce_sp_licitacao(settings.tce_sp_year, settings.tce_sp_month)
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
        tce_rs = resolve_tce_rs_licitacon(settings.tce_rs_year, fetch=False)
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
    return {
        "ocds_jsonl": ocds.jsonl_url,
        "rfb_index": rfb.index_url,
        "rfb_month": rfb.month,
        "pncp_consulta": pncp.consulta_base,
        "pncp_openapi": pncp.consulta_openapi,
        "tce_sp_zip": tce.zip_url,
        "tce_rs_zip": tce_rs.zip_url,
    }


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
    for source in ("ocds", "receita_cnpj", "receita_cnpj_socios", "pncp_consulta"):
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
            if source == "pncp_consulta":
                if df.is_empty():
                    raise SystemExit("pncp_consulta landed empty from fixture")
                ids = {str(v) for v in df["numero_controle_pncp"].to_list()} if "numero_controle_pncp" in df.columns else set()
                if PNCP_COMPRA_1 not in ids or PNCP_COMPRA_2 not in ids:
                    raise SystemExit(f"pncp_consulta fixture missing compras: {ids}")
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
    land_receita_cnpj(settings, store, cnpj_basicos=basicos)
    if len(store.list_parquet("receita_cnpj")) != len(receita_first):
        raise SystemExit("receita reland wrote a second parquet")
    if len(store.list_parquet("receita_cnpj_socios")) != len(socios_first):
        raise SystemExit("receita socios reland wrote a second parquet")
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
    blobs = fetch_raw_text_blobs(settings)
    leaked = [token for token in (TCE_LOSER_CNPJ, TCE_WINNER_CNPJ, TCE_LOSER_PROPOSTA) if token in " ".join(blobs)]
    if leaked:
        raise SystemExit(f"TCE-SP participant proposal leaked into warehouse: {leaked}")


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
    blobs = fetch_raw_text_blobs(settings)
    leaked = [
        token
        for token in (TCE_RS_LOSER_CNPJ, TCE_RS_WINNER_CNPJ, TCE_RS_LOSER_PROPOSTA)
        if token in " ".join(blobs)
    ]
    if leaked:
        raise SystemExit(f"TCE-RS participant proposal leaked into warehouse: {leaked}")


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
