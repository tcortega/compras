from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

from compras_detect.tier1 import run_tier1
from compras_ingest.cpf import assert_no_raw_cpf, mask_cpf
from compras_ingest.landing import LandingStore
from compras_ingest.official import (
    OCDS_OCP_REGISTRY_URL,
    PNCP_API_BASE,
    PNCP_COMPRA_PATH,
    PNCP_CONSULTA_BASE,
    PNCP_CONSULTA_OPENAPI,
    PNCP_CONSULTA_SWAGGER,
    PNCP_ITEM_RESULTADOS_PATH,
    PNCP_ITENS_PATH,
    PNCP_PUBLICACAO_PATH,
    RFB_SHARE_URL,
    PncpOfficial,
    resolve_ocds_feed,
    resolve_pncp_consulta,
    resolve_receita_index,
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
from compras_ingest.warehouse import fetch_contratacao, fetch_flags, fetch_items_for, fetch_one_orgao, fetch_raw_text_blobs, write_flags


ORGAO_CNPJ = "29477000000180"
PNCP_ID = "29477000000180-1-2024-000001"
RAW_CPF = "12345678901"
LANDED_SOURCES = ("compras_gov", "ocds", "receita_cnpj", "receita_cnpj_socios", "pncp_consulta")
PNCP_COMPRA_1 = "29477000000180-1-000001/2024"
PNCP_COMPRA_2 = "29477000000180-1-000002/2024"
EXTRA_ORGAOS = (
    ("28521748000159", "3303302", "RJ"),
    ("46137410000180", "3506003", "SP"),
)


def main() -> int:
    settings = Settings.from_env()
    _check_defs()
    official = _assert_official_urls(settings)
    _assert_pncp_spacing_and_resume(settings)
    result = run_compras_slice(settings)
    _assert_landing(settings, result.landing.sha256)
    _assert_tier_a_landing(settings, result.ocds_report)
    _assert_write_once(settings)
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
    return {
        "ocds_jsonl": ocds.jsonl_url,
        "rfb_index": rfb.index_url,
        "rfb_month": rfb.month,
        "pncp_consulta": pncp.consulta_base,
        "pncp_openapi": pncp.consulta_openapi,
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


def _fetched_sequencial(calls: list[tuple[str, dict]], sequencial: int) -> bool:
    token = f"/compras/2024/{sequencial}"
    return any(token in url and "/itens" in url for url, _ in calls)


if __name__ == "__main__":
    sys.exit(main())
