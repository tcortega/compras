from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

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
USER_AGENT = "compras-ingest/0.1"
_MONTH = re.compile(r"^\d{4}-\d{2}$")
_PROP_NAME = re.compile(r"<d:displayname>([^<]+)</d:displayname>")
_JSONL = re.compile(
    r"""(?:href|contentUrl)\s*[=\:]\s*["']([^"']+?\.jsonl\.gz)["']""",
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
