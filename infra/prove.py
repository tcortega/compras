#!/usr/bin/env python3
"""Hit served API list/get and web home. Fail on stub data or public flag fields."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

API = os.environ.get("API_BASE_URL", "http://127.0.0.1:5080").rstrip("/")
WEB = os.environ.get("WEB_BASE_URL", "http://127.0.0.1:3100").rstrip("/")

STUB_MARKERS = (
    "7c2e1f40-3306-4050",
    "8d3f2a51-3306-4050",
    "9e4a3b62-3306-4050",
    "ae5b4c73-3306-4050",
    "Dipirona",
    "Distribuidora de Medicamentos Serra",
    "sha256:dev-slice-vr-2024",
)
BANNED_COPY = re.compile(r"fraude|corrupto|roubo|flag|ranking", re.I)
FLAG_KEY = re.compile(r"flag", re.I)


def main() -> int:
    orgaos = get_json(f"{API}/api/orgaos?skip=0&take=50")
    deny_flags(orgaos, f"{API}/api/orgaos")
    deny_stub(json.dumps(orgaos, ensure_ascii=False), "api /api/orgaos")
    items_page = orgaos.get("items") or []
    if not items_page:
        raise SystemExit("api /api/orgaos returned no rows")
    orgao = items_page[0]
    razao = str(orgao.get("razaoSocial") or "")
    if "volta redonda" not in razao.casefold():
        raise SystemExit(f"api orgao is not Volta Redonda: {razao}")
    if str(orgao.get("municipioIbge") or "") != "3306305":
        raise SystemExit(f"api orgao IBGE is not 3306305: {orgao.get('municipioIbge')}")
    if str(orgao.get("uf") or "") != "RJ":
        raise SystemExit(f"api orgao UF is not RJ: {orgao.get('uf')}")
    if str(orgao.get("cnpj") or "") == "29138108000113":
        raise SystemExit("api served stub Prefeitura CNPJ")

    oid = orgao["id"]
    got = get_json(f"{API}/api/orgaos/{oid}")
    deny_flags(got, f"{API}/api/orgaos/{oid}")
    deny_stub(json.dumps(got, ensure_ascii=False), "api get orgao")
    if str(got.get("id") or got.get("orgao", {}).get("id") or "") != str(oid):
        raise SystemExit("api get orgao id mismatch")

    items = get_json(f"{API}/api/items?skip=0&take=50")
    deny_flags(items, f"{API}/api/items")
    deny_stub(json.dumps(items, ensure_ascii=False), "api /api/items")
    coverage = items.get("coverage") or {}
    n = coverage.get("n")
    if not isinstance(n, int) or n < 1:
        raise SystemExit(f"api items coverage.n missing or empty: {coverage}")
    rows = items.get("items") or []
    if not rows:
        raise SystemExit("api /api/items returned no rows")
    if any(str(row.get("uf") or "") != "RJ" for row in rows):
        raise SystemExit("api items are not the RJ slice")
    iid = rows[0]["id"]
    item = get_json(f"{API}/api/items/{iid}")
    deny_flags(item, f"{API}/api/items/{iid}")
    deny_stub(json.dumps(item, ensure_ascii=False), "api get item")

    home = get_text(f"{WEB}/")
    deny_stub(home, "web /")
    if BANNED_COPY.search(home):
        raise SystemExit("web / leaked banned copy")
    if "volta redonda" not in home.casefold():
        raise SystemExit("web / missing Volta Redonda")
    if not re.search(r"n=\d+", home):
        raise SystemExit("web / missing coverage n")
    if "UF RJ" not in home:
        raise SystemExit("web / missing UF RJ")
    if not re.search(r"trimestre|trim\.", home, re.I):
        raise SystemExit("web / missing trimestre")
    if not re.search(r"metodologia", home, re.I):
        raise SystemExit("web / missing metodologia")

    orgaos_html = get_text(f"{WEB}/orgaos")
    deny_stub(orgaos_html, "web /orgaos")
    if BANNED_COPY.search(orgaos_html):
        raise SystemExit("web /orgaos leaked banned copy")
    if "volta redonda" not in orgaos_html.casefold():
        raise SystemExit("web /orgaos missing Volta Redonda")

    print("compose prove ok")
    print(f"orgao={razao} ibge={orgao.get('municipioIbge')} items={n}")
    return 0


def get_json(url: str) -> dict:
    raw = get_text(url)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{url} is not JSON") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{url} JSON is not an object")
    return data


def get_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"accept": "application/json, text/html"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise SystemExit(f"{url} status {resp.status}")
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"{url} status {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"{url} unreachable: {exc.reason}") from exc


def deny_stub(blob: str, where: str) -> None:
    for marker in STUB_MARKERS:
        if marker in blob:
            raise SystemExit(f"{where} used stub data ({marker})")


def deny_flags(payload: object, where: str) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if FLAG_KEY.search(str(key)):
                raise SystemExit(f"{where} leaked public flag field {key}")
            deny_flags(value, where)
        return
    if isinstance(payload, list):
        for item in payload:
            deny_flags(item, where)


if __name__ == "__main__":
    sys.exit(main())
