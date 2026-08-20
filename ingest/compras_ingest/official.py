from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

# Live official hosts. Verified 2026-08-20. Do not invent replacements.
OCDS_OPENAPI_URL = "https://dadosabertos.compras.gov.br/v3/api-docs"
OCDS_RELEASES_PATH = "/modulo-ocds/1_releases"
OCDS_PUBLISHER_URL = "https://dadosabertos.compras.gov.br/modulo-ocds/1_releases"
OCDS_OCP_REGISTRY_URL = "https://data.open-contracting.org/en/publication/157"
OCDS_OCP_JSONL_URL = "https://data.open-contracting.org/en/publication/157/download?name={year}.jsonl.gz"

RFB_SHARE_URL = "https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9"
RFB_WEBDAV_URL = "https://arquivos.receitafederal.gov.br/public.php/webdav/"
RFB_SHARE_TOKEN = "YggdBLfdninEJX9"

OCDS_HOSTS = frozenset(
    {
        "dadosabertos.compras.gov.br",
        "data.open-contracting.org",
        "fastly.data.open-contracting.org",
    }
)
RFB_HOSTS = frozenset({"arquivos.receitafederal.gov.br", "dados.gov.br"})
USER_AGENT = "compras-ingest/0.1"
_MONTH = re.compile(r"^\d{4}-\d{2}$")
_PROP_NAME = re.compile(r"<d:displayname>([^<]+)</d:displayname>")


@dataclass(frozen=True)
class OcdsOfficial:
    publisher_url: str
    openapi_url: str
    ocp_registry_url: str
    ocp_jsonl_url: str
    year: int


@dataclass(frozen=True)
class ReceitaOfficial:
    index_url: str
    webdav_root: str
    token: str
    month: str
    files: tuple[str, ...]


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
    """Hit live OpenAPI + OCP registry. Fail if official URL cannot be resolved."""
    jsonl = OCDS_OCP_JSONL_URL.format(year=year)
    with http_client() as client:
        spec = _get_json(client, OCDS_OPENAPI_URL, OCDS_HOSTS)
        paths = spec.get("paths") or {}
        if OCDS_RELEASES_PATH not in paths:
            raise RuntimeError(f"OpenAPI missing {OCDS_RELEASES_PATH}")
        _require_ok(client, OCDS_OCP_REGISTRY_URL, OCDS_HOSTS)
        _require_ok(client, jsonl, OCDS_HOSTS)
    return OcdsOfficial(
        publisher_url=OCDS_PUBLISHER_URL,
        openapi_url=OCDS_OPENAPI_URL,
        ocp_registry_url=OCDS_OCP_REGISTRY_URL,
        ocp_jsonl_url=jsonl,
        year=year,
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


def _get_json(client: httpx.Client, url: str, allowed: frozenset[str]) -> dict:
    assert_official_host(url, allowed)
    resp = client.get(url)
    resp.raise_for_status()
    assert_official_host(str(resp.url), allowed)
    data = resp.json()
    if not isinstance(data, dict):
        raise RuntimeError(f"expected JSON object from {url}")
    return data


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
