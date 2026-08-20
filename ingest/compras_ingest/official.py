from __future__ import annotations

import re
import time
from dataclasses import dataclass
from html import unescape
from urllib.parse import unquote, urljoin

import httpx

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
    if year < 2014:
        raise RuntimeError(f"TCE-RS year out of range: {year}")
    portal = tce_rs_portal_url(year)
    ckan = tce_rs_ckan_url(year)
    assert_official_host(portal, TCE_RS_HOSTS)
    assert_official_host(ckan, TCE_RS_HOSTS)
    assert_official_host(TCE_RS_EXAMPLE_URL, TCE_RS_HOSTS)
    assert_official_host(TCE_RS_LEIAUTE_URL, TCE_RS_HOSTS)
    zip_url = TCE_RS_EXAMPLE_URL
    via = "example"
    if fetch:
        try:
            zip_url = _ckan_zip_with_retry(ckan, year)
            via = "ckan"
        except Exception:
            zip_url = TCE_RS_EXAMPLE_URL
            via = "example"
    return TceRsOfficial(portal, ckan, zip_url, TCE_RS_EXAMPLE_URL, TCE_RS_LEIAUTE_URL, year, via)


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
