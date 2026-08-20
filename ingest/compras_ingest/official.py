from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from html import unescape
from urllib.parse import unquote, urljoin

import httpx

# Fixture e2e sets this. resolve_* must not run off official hosts in that mode.
RESOLVE_DENIED = False

# BUILD_SPEC Tier A source 2. Live page verified 2026-08-20.
OCDS_OCP_REGISTRY_URL = "https://data.open-contracting.org/en/publication/157"

# BUILD_SPEC Tier A source 4. Live RFB Nextcloud index verified 2026-08-20.
RFB_SHARE_URL = "https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9"
RFB_WEBDAV_URL = "https://arquivos.receitafederal.gov.br/public.php/webdav/"
RFB_SHARE_TOKEN = "YggdBLfdninEJX9"

# BUILD_SPEC Tier B source 5. Live OpenAPI verified 2026-08-20.
PNCP_CONSULTA_BASE = "https://pncp.gov.br/api/consulta"
PNCP_CONSULTA_OPENAPI = "https://pncp.gov.br/api/consulta/v3/api-docs"
PNCP_CONSULTA_SWAGGER = "https://pncp.gov.br/api/consulta/swagger-ui/index.html"
# Items are not on consulta (live 404). Same host, /api/pncp swagger verified 2026-08-20.
PNCP_API_BASE = "https://pncp.gov.br/api/pncp"
PNCP_API_OPENAPI = "https://pncp.gov.br/api/pncp/v3/api-docs"
PNCP_PUBLICACAO_PATH = "/v1/contratacoes/publicacao"
PNCP_COMPRA_PATH = "/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}"
PNCP_ITENS_PATH = "/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens"
PNCP_ITEM_RESULTADOS_PATH = "/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens/{numeroItem}/resultados"
PNCP_MODALIDADES_PATH = "/v1/modalidades"

OCDS_HOSTS = frozenset({"data.open-contracting.org", "fastly.data.open-contracting.org"})
RFB_HOSTS = frozenset({"arquivos.receitafederal.gov.br"})
PNCP_HOSTS = frozenset({"pncp.gov.br"})
# BUILD_SPEC Tier A source 1. Index listed 2026-08-20.
COMPRAS_GOV_INDEX = "https://repositorio.dados.gov.br/seges/comprasgov/"
COMPRAS_GOV_HOSTS = frozenset({"repositorio.dados.gov.br"})
# BUILD_SPEC Tier B source 6. Listing verified 2026-08-20. Cubo SQL is not this extract.
TCE_SP_LISTING_URL = "https://transparencia.tce.sp.gov.br/conjunto-de-dados"
TCE_SP_HOSTS = frozenset({"transparencia.tce.sp.gov.br"})
# BUILD_SPEC Tier B source 6. Portal and leiaute verified 2026-08-20 in docs/tce-probe.md.
TCE_RS_PORTAL_BASE = "https://dados.tce.rs.gov.br/dataset/licitacoes-consolidado"
TCE_RS_CKAN_PACKAGE = "https://dados.tce.rs.gov.br/api/3/action/package_show?id=licitacoes-consolidado-{year}"
TCE_RS_LEIAUTE_URL = "https://tcers.tc.br/repo/cex/licitacon/cpt/eValidador_LicitaCon_Manual_Leiaute_1.4.pdf"
TCE_RS_EXAMPLE_URL = "https://tcers.tc.br/repo/cex/licitacon/cpt/eValidador-licitacon-exemplos-1.4.zip"
TCE_RS_HOSTS = frozenset({"dados.tce.rs.gov.br", "tcers.tc.br"})
TCE_RS_FETCH_ATTEMPTS = 4
# BUILD_SPEC Tier C source 7. Live Portal download verified 2026-08-20.
# Listing https://portaldatransparencia.gov.br/download-de-dados/{ceis|cnep}/YYYYMMDD
# redirects to dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida/{ceis|cnep}/YYYYMMDD_{CEIS|CNEP}.zip
CGU_CEIS_LISTING_URL = "https://portaldatransparencia.gov.br/download-de-dados/ceis"
CGU_CNEP_LISTING_URL = "https://portaldatransparencia.gov.br/download-de-dados/cnep"
CGU_ZIP_ROOT = "https://dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida"
CGU_HOSTS = frozenset({"portaldatransparencia.gov.br", "dadosabertos-download.cgu.gov.br"})
CGU_FETCH_LOOKBACK_DAYS = 14
OFFICIAL_HOSTS = (
    OCDS_HOSTS | RFB_HOSTS | PNCP_HOSTS | TCE_SP_HOSTS | TCE_RS_HOSTS | CGU_HOSTS | COMPRAS_GOV_HOSTS
)
USER_AGENT = "compras-ingest/0.1"
_MONTH = re.compile(r"^\d{4}-\d{2}$")
_PROP_NAME = re.compile(r"<d:displayname>([^<]+)</d:displayname>")
_JSONL = re.compile(
    r"""(?:href|contentUrl)\s*[=\:]\s*["']([^"']+?\.jsonl\.gz)["']""",
    re.IGNORECASE,
)
_HREF = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_LICITACAO_ZIP = re.compile(
    r"licitacao-(\d{4})(?:-(\d{2}))?(?:_\d+)?\.zip$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ComprasGovOfficial:
    index_url: str
    year: int
    cadence: str
    compra_url: str
    item_url: str


@dataclass(frozen=True)
class OcdsOfficial:
    registry_url: str
    jsonl_url: str
    year: int


@dataclass(frozen=True)
class ReceitaOfficial:
    index_url: str
    webdav_root: str
    token: str
    month: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class PncpOfficial:
    consulta_base: str
    consulta_openapi: str
    swagger_url: str
    api_base: str
    publicacao_path: str
    compra_path: str
    itens_path: str
    resultados_path: str
    modalidades: tuple[int, ...]


@dataclass(frozen=True)
class TceSpOfficial:
    listing_url: str
    zip_url: str
    year: int
    month: int


@dataclass(frozen=True)
class TceRsOfficial:
    portal_url: str
    ckan_url: str
    zip_url: str
    example_url: str
    leiaute_url: str
    year: int
    via: str


@dataclass(frozen=True)
class CguCeisCnepOfficial:
    listing_ceis: str
    listing_cnep: str
    ceis_download_url: str
    cnep_download_url: str
    ceis_zip_url: str
    cnep_zip_url: str
    day: date


def deny_resolve(denied: bool = True) -> None:
    global RESOLVE_DENIED
    RESOLVE_DENIED = denied


def _check_resolve(name: str) -> None:
    if RESOLVE_DENIED:
        raise RuntimeError(f"fixture mode called {name}")


def http_client(timeout: float = 45.0) -> httpx.Client:
    return httpx.Client(
        timeout=httpx.Timeout(timeout, connect=15.0),
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        follow_redirects=True,
    )


def assert_official_host(url: str, allowed: frozenset[str]) -> str:
    host = httpx.URL(url).host or ""
    if host not in allowed:
        raise RuntimeError(f"refusing non-official host {host} for {url}")
    return host


def resolve_ocds_feed(year: int) -> OcdsOfficial:
    """Read live OCP publication 157. Fail if its jsonl download cannot be resolved."""
    _check_resolve("resolve_ocds_feed")
    with http_client() as client:
        resp = client.get(OCDS_OCP_REGISTRY_URL)
        resp.raise_for_status()
        assert_official_host(str(resp.url), OCDS_HOSTS)
        download = _ocp_jsonl_from_page(resp.text, year)
        if not download:
            raise RuntimeError("OCP publication 157 page has no jsonl download")
        assert_official_host(download, OCDS_HOSTS)
        if "/publication/157/" not in download:
            raise RuntimeError(f"OCDS download is not publication 157: {download}")
        _require_ok(client, download, OCDS_HOSTS)
    return OcdsOfficial(OCDS_OCP_REGISTRY_URL, download, year)


def resolve_pncp_consulta() -> PncpOfficial:
    """Hit live PNCP OpenAPI. Fail if official consulta or items paths cannot be resolved."""
    _check_resolve("resolve_pncp_consulta")
    with http_client() as client:
        consulta = _require_json(client, PNCP_CONSULTA_OPENAPI, PNCP_HOSTS)
        _require_openapi_path(consulta, PNCP_PUBLICACAO_PATH)
        _require_openapi_path(consulta, PNCP_COMPRA_PATH)
        if _openapi_has_path(consulta, PNCP_ITENS_PATH):
            raise RuntimeError("consulta OpenAPI unexpectedly lists items; re-verify before changing hosts")
        pncp = _require_json(client, PNCP_API_OPENAPI, PNCP_HOSTS)
        _require_openapi_path(pncp, PNCP_ITENS_PATH)
        _require_openapi_path(pncp, PNCP_ITEM_RESULTADOS_PATH)
        _require_openapi_path(pncp, PNCP_MODALIDADES_PATH)
        mods = _modalidade_ids(client)
    return PncpOfficial(
        PNCP_CONSULTA_BASE,
        PNCP_CONSULTA_OPENAPI,
        PNCP_CONSULTA_SWAGGER,
        PNCP_API_BASE,
        PNCP_PUBLICACAO_PATH,
        PNCP_COMPRA_PATH,
        PNCP_ITENS_PATH,
        PNCP_ITEM_RESULTADOS_PATH,
        mods,
    )


def resolve_tce_sp_licitacao(year: int, month: int) -> TceSpOfficial:
    """Read live TCE-SP listing. Fail if the year/month licitacao zip is not official."""
    _check_resolve("resolve_tce_sp_licitacao")
    if month < 1 or month > 12:
        raise RuntimeError(f"TCE-SP month out of range: {month}")
    with http_client() as client:
        resp = client.get(TCE_SP_LISTING_URL)
        resp.raise_for_status()
        assert_official_host(str(resp.url), TCE_SP_HOSTS)
        zip_url = licitacao_zip_from_listing(resp.text, year, month, str(resp.url))
        _require_zip_reachable(client, zip_url, TCE_SP_HOSTS)
    return TceSpOfficial(TCE_SP_LISTING_URL, zip_url, year, month)


def tce_rs_portal_url(year: int) -> str:
    return f"{TCE_RS_PORTAL_BASE}-{year}"


def tce_rs_ckan_url(year: int) -> str:
    return TCE_RS_CKAN_PACKAGE.format(year=year)


def resolve_tce_rs_licitacon(year: int, fetch: bool = False) -> TceRsOfficial:
    """Resolve official TCE-RS LicitaCon URLs. Live CKAN is fetch-only."""
    if fetch:
        _check_resolve("resolve_tce_rs_licitacon")
    official = fixture_tce_rs_official(year)
    if not fetch:
        return official
    try:
        zip_url = _ckan_zip_with_retry(official.ckan_url, year)
        return TceRsOfficial(
            official.portal_url,
            official.ckan_url,
            zip_url,
            official.example_url,
            official.leiaute_url,
            year,
            "ckan",
        )
    except Exception:
        return official


def fixture_receita_official() -> ReceitaOfficial:
    return ReceitaOfficial(
        RFB_SHARE_URL,
        RFB_WEBDAV_URL,
        RFB_SHARE_TOKEN,
        "2024-12",
        ("Empresas0.zip", "Estabelecimentos0.zip", "Socios0.zip"),
    )


def compras_gov_anual_compra_url(base: str, year: int) -> str:
    root = base.rstrip("/")
    return f"{root}/anual/{year}/comprasGOV-anual-VW_FT_PNCP_COMPRA-{year}.csv"


def compras_gov_anual_item_url(base: str, year: int) -> str:
    root = base.rstrip("/")
    return f"{root}/anual/{year}/comprasGOV-anual-VW_FT_PNCP_COMPRA_ITEM-{year}.csv"


def compras_gov_diario_compra_url(base: str, day: date) -> str:
    # Live index 2026-08-20: diario/YYYY/MM/DD/comprasGOV-diario-VW_FT_PNCP_COMPRA-YYYY-MM-DD.csv
    root = base.rstrip("/")
    return (
        f"{root}/diario/{day.year}/{day.month:02d}/{day.day:02d}/"
        f"comprasGOV-diario-VW_FT_PNCP_COMPRA-{day.isoformat()}.csv"
    )


def compras_gov_diario_item_url(base: str, day: date) -> str:
    root = base.rstrip("/")
    return (
        f"{root}/diario/{day.year}/{day.month:02d}/{day.day:02d}/"
        f"comprasGOV-diario-VW_FT_PNCP_COMPRA_ITEM-{day.isoformat()}.csv"
    )


def compras_gov_mensal_compra_url(base: str, year: int, month: int) -> str:
    # Live index 2026-08-20: mensal/YYYY/MM/comprasGOV-mensal-VW_FT_PNCP_COMPRA-YYYY-MM.csv
    if month < 1 or month > 12:
        raise RuntimeError(f"Compras.gov month out of range: {month}")
    root = base.rstrip("/")
    return f"{root}/mensal/{year}/{month:02d}/comprasGOV-mensal-VW_FT_PNCP_COMPRA-{year}-{month:02d}.csv"


def compras_gov_mensal_item_url(base: str, year: int, month: int) -> str:
    if month < 1 or month > 12:
        raise RuntimeError(f"Compras.gov month out of range: {month}")
    root = base.rstrip("/")
    return f"{root}/mensal/{year}/{month:02d}/comprasGOV-mensal-VW_FT_PNCP_COMPRA_ITEM-{year}-{month:02d}.csv"


def fixture_compras_gov_diario_official(
    day: date, base: str = COMPRAS_GOV_INDEX.rstrip("/")
) -> ComprasGovOfficial:
    """Build official diario COMPRA+ITEM URLs. Does not contact hosts."""
    compra = compras_gov_diario_compra_url(base, day)
    item = compras_gov_diario_item_url(base, day)
    return _compras_gov_official(COMPRAS_GOV_INDEX, day.year, "diario", compra, item, day=day)


def fixture_compras_gov_mensal_official(
    year: int, month: int, base: str = COMPRAS_GOV_INDEX.rstrip("/")
) -> ComprasGovOfficial:
    """Build official mensal COMPRA+ITEM URLs. Does not contact hosts."""
    compra = compras_gov_mensal_compra_url(base, year, month)
    item = compras_gov_mensal_item_url(base, year, month)
    return _compras_gov_official(COMPRAS_GOV_INDEX, year, "mensal", compra, item, month=month)


def resolve_compras_gov_incremental(
    day: date, base: str = COMPRAS_GOV_INDEX.rstrip("/")
) -> ComprasGovOfficial:
    """HEAD official diario COMPRA+ITEM for that day. Else mensal for that month. Fetch-only."""
    _check_resolve("resolve_compras_gov_incremental")
    daily = fixture_compras_gov_diario_official(day, base)
    if _compras_gov_pair_ok(daily):
        return daily
    monthly = fixture_compras_gov_mensal_official(day.year, day.month, base)
    if _compras_gov_pair_ok(monthly):
        return monthly
    raise RuntimeError(
        f"compras.gov diario {day.isoformat()} and mensal {day.year}-{day.month:02d} COMPRA+ITEM missing"
    )


def _compras_gov_pair_ok(official: ComprasGovOfficial) -> bool:
    with http_client() as client:
        try:
            _require_ok(client, official.compra_url, COMPRAS_GOV_HOSTS)
            _require_ok(client, official.item_url, COMPRAS_GOV_HOSTS)
        except Exception:
            return False
    return True


def _compras_gov_official(
    index_url: str,
    year: int,
    cadence: str,
    compra: str,
    item: str,
    day: date | None = None,
    month: int | None = None,
) -> ComprasGovOfficial:
    assert_official_host(compra, COMPRAS_GOV_HOSTS)
    assert_official_host(item, COMPRAS_GOV_HOSTS)
    token = {
        "anual": f"/anual/{year}/comprasGOV-anual-VW_FT_PNCP_COMPRA-{year}.csv",
        "diario": f"/diario/{year}/" + (f"{day.month:02d}/{day.day:02d}/comprasGOV-diario-VW_FT_PNCP_COMPRA-{day.isoformat()}.csv" if day else ""),
        "mensal": f"/mensal/{year}/" + (f"{month:02d}/comprasGOV-mensal-VW_FT_PNCP_COMPRA-{year}-{month:02d}.csv" if month else ""),
    }
    need = token.get(cadence, "")
    if not need or need not in compra:
        raise RuntimeError(f"COMPRA URL is not the official {cadence} file: {compra}")
    item_need = need.replace("VW_FT_PNCP_COMPRA-", "VW_FT_PNCP_COMPRA_ITEM-")
    if item_need not in item:
        raise RuntimeError(f"ITEM URL is not the official {cadence} file: {item}")
    if "COMPRA_ITEM" in compra.split("/")[-1]:
        raise RuntimeError(f"COMPRA URL pointed at ITEM: {compra}")
    return ComprasGovOfficial(index_url, year, cadence, compra, item)


def fixture_compras_gov_official(year: int, base: str = COMPRAS_GOV_INDEX.rstrip("/")) -> ComprasGovOfficial:
    """Build official anual COMPRA+ITEM URLs. Does not contact hosts."""
    if year < 2021:
        raise RuntimeError(f"Compras.gov year out of range: {year}")
    compra = compras_gov_anual_compra_url(base, year)
    item = compras_gov_anual_item_url(base, year)
    return _compras_gov_official(COMPRAS_GOV_INDEX, year, "anual", compra, item)


def fixture_ocds_official(year: int) -> OcdsOfficial:
    return OcdsOfficial(
        OCDS_OCP_REGISTRY_URL,
        f"https://data.open-contracting.org/en/publication/157/download?name={year}.jsonl.gz",
        year,
    )


def fixture_tce_sp_official(year: int, month: int) -> TceSpOfficial:
    if month < 1 or month > 12:
        raise RuntimeError(f"TCE-SP month out of range: {month}")
    zip_url = (
        "https://transparencia.tce.sp.gov.br/sites/default/files/"
        f"conjunto-dados/licitacoes-contratos/licitacao-{year}-{month:02d}.zip"
    )
    return TceSpOfficial(TCE_SP_LISTING_URL, zip_url, year, month)


def fixture_tce_rs_official(year: int) -> TceRsOfficial:
    if year < 2014:
        raise RuntimeError(f"TCE-RS year out of range: {year}")
    portal = tce_rs_portal_url(year)
    ckan = tce_rs_ckan_url(year)
    assert_official_host(portal, TCE_RS_HOSTS)
    assert_official_host(ckan, TCE_RS_HOSTS)
    assert_official_host(TCE_RS_EXAMPLE_URL, TCE_RS_HOSTS)
    assert_official_host(TCE_RS_LEIAUTE_URL, TCE_RS_HOSTS)
    return TceRsOfficial(
        portal,
        ckan,
        TCE_RS_EXAMPLE_URL,
        TCE_RS_EXAMPLE_URL,
        TCE_RS_LEIAUTE_URL,
        year,
        "example",
    )


def cgu_listing_url(cadastro: str) -> str:
    token = cadastro.strip().lower()
    if token == "ceis":
        return CGU_CEIS_LISTING_URL
    if token == "cnep":
        return CGU_CNEP_LISTING_URL
    raise RuntimeError(f"CGU cadastro is not CEIS or CNEP: {cadastro}")


def cgu_download_url(cadastro: str, day: date) -> str:
    return f"{cgu_listing_url(cadastro)}/{day.strftime('%Y%m%d')}"


def cgu_zip_url(cadastro: str, day: date) -> str:
    token = cadastro.strip().lower()
    if token not in {"ceis", "cnep"}:
        raise RuntimeError(f"CGU cadastro is not CEIS or CNEP: {cadastro}")
    return f"{CGU_ZIP_ROOT}/{token}/{day.strftime('%Y%m%d')}_{token.upper()}.zip"


def assert_cgu_zip_url(url: str, cadastro: str) -> str:
    """Refuse mirrors. Zip must be the official CGU saida extract."""
    assert_official_host(url, CGU_HOSTS)
    host = httpx.URL(url).host or ""
    if host != "dadosabertos-download.cgu.gov.br":
        raise RuntimeError(f"CGU zip host is not official: {url}")
    token = cadastro.strip().lower()
    path = (httpx.URL(url).path or "").lower()
    if f"/portaldatransparencia/saida/{token}/" not in path:
        raise RuntimeError(f"CGU download is not the {token} saida zip: {url}")
    if not path.endswith(f"_{token}.zip"):
        raise RuntimeError(f"CGU download is not the {token} saida zip: {url}")
    return url


def fixture_cgu_ceis_cnep_official(day: date | None = None) -> CguCeisCnepOfficial:
    """Build official CEIS/CNEP URLs. Does not contact hosts."""
    chosen = day or date(2024, 3, 15)
    official = CguCeisCnepOfficial(
        CGU_CEIS_LISTING_URL,
        CGU_CNEP_LISTING_URL,
        cgu_download_url("ceis", chosen),
        cgu_download_url("cnep", chosen),
        cgu_zip_url("ceis", chosen),
        cgu_zip_url("cnep", chosen),
        chosen,
    )
    _assert_cgu_official(official)
    return official


def resolve_cgu_ceis_cnep(day: date | None = None) -> CguCeisCnepOfficial:
    """Read live Portal da Transparencia dated downloads. Fetch-only."""
    _check_resolve("resolve_cgu_ceis_cnep")
    start = day or datetime.now(timezone.utc).date()
    last: Exception | None = None
    with http_client() as client:
        _require_ok(client, CGU_CEIS_LISTING_URL, CGU_HOSTS)
        _require_ok(client, CGU_CNEP_LISTING_URL, CGU_HOSTS)
        for i in range(CGU_FETCH_LOOKBACK_DAYS):
            cand = start - timedelta(days=i)
            try:
                ceis_dl, ceis_zip = _resolve_cgu_cadastro(client, "ceis", cand)
                cnep_dl, cnep_zip = _resolve_cgu_cadastro(client, "cnep", cand)
                official = CguCeisCnepOfficial(
                    CGU_CEIS_LISTING_URL,
                    CGU_CNEP_LISTING_URL,
                    ceis_dl,
                    cnep_dl,
                    ceis_zip,
                    cnep_zip,
                    cand,
                )
                _assert_cgu_official(official)
                return official
            except Exception as exc:
                last = exc
    raise RuntimeError(
        f"CGU CEIS/CNEP download date could not be resolved after {CGU_FETCH_LOOKBACK_DAYS} days"
    ) from last


def _assert_cgu_official(official: CguCeisCnepOfficial) -> None:
    if official.listing_ceis != CGU_CEIS_LISTING_URL:
        raise RuntimeError(f"CEIS listing URL is not official: {official.listing_ceis}")
    if official.listing_cnep != CGU_CNEP_LISTING_URL:
        raise RuntimeError(f"CNEP listing URL is not official: {official.listing_cnep}")
    for url in (
        official.listing_ceis,
        official.listing_cnep,
        official.ceis_download_url,
        official.cnep_download_url,
        official.ceis_zip_url,
        official.cnep_zip_url,
    ):
        assert_official_host(url, CGU_HOSTS)
    if official.ceis_download_url != cgu_download_url("ceis", official.day):
        raise RuntimeError(f"CEIS download URL is not official: {official.ceis_download_url}")
    if official.cnep_download_url != cgu_download_url("cnep", official.day):
        raise RuntimeError(f"CNEP download URL is not official: {official.cnep_download_url}")
    assert_cgu_zip_url(official.ceis_zip_url, "ceis")
    assert_cgu_zip_url(official.cnep_zip_url, "cnep")


def _resolve_cgu_cadastro(client: httpx.Client, cadastro: str, day: date) -> tuple[str, str]:
    download = cgu_download_url(cadastro, day)
    assert_official_host(download, CGU_HOSTS)
    resp = client.head(download)
    if resp.status_code in {405, 403}:
        resp = client.get(download)
    if resp.status_code >= 400:
        raise RuntimeError(f"official URL {download} returned {resp.status_code}")
    assert_official_host(str(resp.url), CGU_HOSTS)
    zip_url = str(resp.url)
    if not zip_url.lower().endswith(".zip"):
        loc = resp.headers.get("location") or ""
        zip_url = loc if loc.lower().endswith(".zip") else cgu_zip_url(cadastro, day)
    assert_cgu_zip_url(zip_url, cadastro)
    _require_zip_reachable(client, zip_url, CGU_HOSTS)
    return download, zip_url


def fixture_pncp_official() -> PncpOfficial:
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


def ckan_zip_from_package(payload: dict, year: int) -> str:
    """Pick licitacoes-consolidado-YYYY zip. Refuse non-official hosts."""
    result = payload.get("result") if isinstance(payload, dict) else None
    resources = result.get("resources") if isinstance(result, dict) else None
    if not isinstance(resources, list) or not resources:
        raise RuntimeError("TCE-RS CKAN package has no resources")
    want = f"licitacoes-consolidado-{year}"
    zips: list[str] = []
    for raw in resources:
        if not isinstance(raw, dict):
            continue
        url = str(raw.get("url") or "")
        name = f"{raw.get('name') or ''} {url}"
        if not url:
            continue
        folded = name.lower()
        if want not in folded:
            continue
        if not url.lower().split("?", 1)[0].endswith(".zip"):
            continue
        assert_official_host(url, TCE_RS_HOSTS)
        zips.append(url)
    if not zips:
        raise RuntimeError(f"TCE-RS CKAN package has no {want} zip")
    chosen = zips[0]
    assert_official_host(chosen, TCE_RS_HOSTS)
    return chosen


def licitacao_zip_from_listing(html: str, year: int, month: int, listing_url: str) -> str:
    """Pick the official licitacao-YYYY-MM zip. Refuse cubo SQL and non-official hosts."""
    monthly: list[str] = []
    annual: list[str] = []
    for raw in _HREF.findall(html):
        abs_url = urljoin(listing_url, unquote(unescape(raw)))
        name = (httpx.URL(abs_url).path or "").rsplit("/", 1)[-1]
        match = _LICITACAO_ZIP.search(name)
        if not match:
            continue
        found_year = int(match.group(1))
        found_month = int(match.group(2)) if match.group(2) else None
        if found_year != year:
            continue
        if found_month is not None and found_month != month:
            continue
        if found_month is None and year != 2018:
            continue
        assert_official_host(abs_url, TCE_SP_HOSTS)
        if "/licitacoes-contratos/licitacao-" not in abs_url:
            raise RuntimeError(f"TCE-SP download is not a licitacao zip: {abs_url}")
        if "cubo" in abs_url.lower():
            raise RuntimeError(f"TCE-SP cubo SQL is not the licitacao extract: {abs_url}")
        if found_month is None:
            annual.append(abs_url)
        else:
            monthly.append(abs_url)
    chosen = _prefer_month_zip(monthly) or (annual[0] if annual else "")
    if not chosen:
        raise RuntimeError(f"TCE-SP listing has no licitacao-{year}-{month:02d} zip")
    assert_official_host(chosen, TCE_SP_HOSTS)
    return chosen


def resolve_receita_index() -> ReceitaOfficial:
    """Hit live RFB Nextcloud share. Fail if official index cannot be resolved."""
    _check_resolve("resolve_receita_index")
    with http_client() as client:
        _require_ok(client, RFB_SHARE_URL, RFB_HOSTS)
        months = _webdav_names(client, RFB_WEBDAV_URL, RFB_SHARE_TOKEN)
        dated = sorted(n for n in months if _MONTH.fullmatch(n))
        if not dated:
            raise RuntimeError("RFB share has no YYYY-MM folders")
        month = dated[-1]
        files = _webdav_names(client, f"{RFB_WEBDAV_URL}{month}/", RFB_SHARE_TOKEN)
        needed = ("Empresas", "Estabelecimentos", "Socios")
        missing = [n for n in needed if not any(f.startswith(n) and f.endswith(".zip") for f in files)]
        if missing:
            raise RuntimeError(f"RFB {month} missing {missing}")
    zips = tuple(sorted(f for f in files if f.endswith(".zip")))
    return ReceitaOfficial(RFB_SHARE_URL, RFB_WEBDAV_URL, RFB_SHARE_TOKEN, month, zips)


def download_to(
    client: httpx.Client,
    url: str,
    dest,
    allowed: frozenset[str],
    auth: tuple[str, str] | None = None,
) -> None:
    assert_official_host(url, allowed)
    with client.stream("GET", url, auth=auth) as resp:
        resp.raise_for_status()
        assert_official_host(str(resp.url), allowed)
        for chunk in resp.iter_bytes(1024 * 256):
            if chunk:
                dest.write(chunk)
        dest.flush()


def download_to_retry(
    client: httpx.Client,
    url: str,
    dest,
    allowed: frozenset[str],
    auth: tuple[str, str] | None = None,
    attempts: int = TCE_RS_FETCH_ATTEMPTS,
) -> None:
    last: Exception | None = None
    for i in range(max(1, attempts)):
        try:
            if hasattr(dest, "seek"):
                dest.seek(0)
                dest.truncate()
            download_to(client, url, dest, allowed, auth=auth)
            return
        except Exception as exc:
            last = exc
            if i + 1 < attempts:
                time.sleep(0.25 * (2**i))
    raise RuntimeError(f"official download failed after {attempts} tries: {url}") from last


def _ocp_jsonl_from_page(html: str, year: int) -> str:
    found: list[str] = []
    for raw in _JSONL.findall(html):
        abs_url = urljoin(OCDS_OCP_REGISTRY_URL, raw)
        if "data.open-contracting.org" not in abs_url:
            continue
        if "/publication/157/" not in abs_url:
            continue
        if not abs_url.endswith(".jsonl.gz"):
            continue
        found.append(abs_url)
    if not found:
        return ""
    year_name = f"name={year}.jsonl.gz"
    for url in found:
        if year_name in url:
            return url
    for url in found:
        if "name=full.jsonl.gz" in url:
            return url
    return found[0]


def _require_json(client: httpx.Client, url: str, allowed: frozenset[str]) -> dict:
    assert_official_host(url, allowed)
    resp = client.get(url)
    resp.raise_for_status()
    assert_official_host(str(resp.url), allowed)
    payload = resp.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"official JSON {url} is not an object")
    return payload


def _openapi_has_path(spec: dict, path: str) -> bool:
    paths = spec.get("paths")
    return isinstance(paths, dict) and path in paths


def _require_openapi_path(spec: dict, path: str) -> None:
    if not _openapi_has_path(spec, path):
        raise RuntimeError(f"official OpenAPI missing {path}")


def _modalidade_ids(client: httpx.Client) -> tuple[int, ...]:
    url = f"{PNCP_API_BASE}{PNCP_MODALIDADES_PATH}"
    assert_official_host(url, PNCP_HOSTS)
    resp = client.get(url)
    resp.raise_for_status()
    assert_official_host(str(resp.url), PNCP_HOSTS)
    rows = resp.json()
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("PNCP modalidades list is empty")
    ids = []
    for row in rows:
        if not isinstance(row, dict) or row.get("id") is None:
            continue
        ids.append(int(row["id"]))
    if not ids:
        raise RuntimeError("PNCP modalidades have no ids")
    return tuple(ids)


def _ckan_zip_with_retry(ckan_url: str, year: int) -> str:
    last: Exception | None = None
    with httpx.Client(
        timeout=httpx.Timeout(12.0, connect=4.0),
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        follow_redirects=True,
    ) as client:
        for i in range(TCE_RS_FETCH_ATTEMPTS):
            try:
                payload = _require_json(client, ckan_url, TCE_RS_HOSTS)
                zip_url = ckan_zip_from_package(payload, year)
                _require_zip_reachable(client, zip_url, TCE_RS_HOSTS)
                return zip_url
            except Exception as exc:
                last = exc
                if i + 1 < TCE_RS_FETCH_ATTEMPTS:
                    time.sleep(0.25 * (2**i))
    raise RuntimeError(f"TCE-RS CKAN resolve failed after {TCE_RS_FETCH_ATTEMPTS} tries") from last


def _prefer_month_zip(urls: list[str]) -> str:
    if not urls:
        return ""
    exact = []
    for url in urls:
        name = (httpx.URL(url).path or "").rsplit("/", 1)[-1]
        if re.search(r"licitacao-\d{4}-\d{2}\.zip$", name, re.I):
            exact.append(url)
    return exact[0] if exact else urls[0]


def _require_zip_reachable(client: httpx.Client, url: str, allowed: frozenset[str]) -> None:
    assert_official_host(url, allowed)
    resp = client.head(url)
    if resp.status_code in {405, 403}:
        with client.stream("GET", url) as streamed:
            streamed.raise_for_status()
            assert_official_host(str(streamed.url), allowed)
        return
    if resp.status_code >= 400:
        raise RuntimeError(f"official URL {url} returned {resp.status_code}")
    assert_official_host(str(resp.url), allowed)


def _require_ok(client: httpx.Client, url: str, allowed: frozenset[str]) -> None:
    assert_official_host(url, allowed)
    resp = client.head(url)
    if resp.status_code in {405, 403}:
        resp = client.get(url)
    if resp.status_code >= 400:
        raise RuntimeError(f"official URL {url} returned {resp.status_code}")
    assert_official_host(str(resp.url), allowed)


def _webdav_names(client: httpx.Client, url: str, token: str) -> list[str]:
    assert_official_host(url, RFB_HOSTS)
    body = (
        '<?xml version="1.0"?>'
        '<d:propfind xmlns:d="DAV:">'
        "<d:prop><d:displayname/><d:resourcetype/></d:prop>"
        "</d:propfind>"
    )
    resp = client.request(
        "PROPFIND",
        url,
        content=body,
        auth=(token, ""),
        headers={"Depth": "1", "Content-Type": "application/xml"},
    )
    if resp.status_code not in {207, 200}:
        raise RuntimeError(f"RFB WebDAV {url} returned {resp.status_code}")
    return [n for n in _PROP_NAME.findall(resp.text) if n and n not in {"CNPJ"}]
