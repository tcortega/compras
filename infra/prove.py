#!/usr/bin/env python3
"""Hit served API list/get and web pages. Fail on stub data or public flag fields."""

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
STAT_HOMOLOGADO = re.compile(r'class="kicker">Homologado')
PUBLISHED = {
    "3306305": ("volta redonda", "RJ"),
    "3303302": ("niteroi", "RJ"),
    "3506003": ("bauru", "SP"),
}


def main() -> int:
    orgaos = get_json(f"{API}/api/orgaos?skip=0&take=50")
    deny_flags(orgaos, f"{API}/api/orgaos")
    deny_stub(json.dumps(orgaos, ensure_ascii=False), "api /api/orgaos")
    items_page = orgaos.get("items") or []
    if len(items_page) < 3:
        raise SystemExit(f"api /api/orgaos returned {len(items_page)} rows, need the published slice")
    by_ibge = {str(row.get("municipioIbge") or ""): row for row in items_page}
    for ibge, (nome, uf) in PUBLISHED.items():
        row = by_ibge.get(ibge)
        if row is None:
            raise SystemExit(f"api /api/orgaos missing IBGE {ibge}")
        razao = str(row.get("razaoSocial") or "")
        if nome not in razao.casefold():
            raise SystemExit(f"api orgao {ibge} razao is not {nome}: {razao}")
        if str(row.get("uf") or "") != uf:
            raise SystemExit(f"api orgao {ibge} UF is not {uf}: {row.get('uf')}")
        if str(row.get("cnpj") or "") == "29138108000113":
            raise SystemExit("api served stub Prefeitura CNPJ")
    orgao_cov = orgaos.get("coverage") or {}
    if orgao_cov.get("uf") not in (None, ""):
        raise SystemExit(f"mixed orgao list invented a UF: {orgao_cov}")
    if not isinstance(orgao_cov.get("n"), int) or orgao_cov["n"] < 3:
        raise SystemExit(f"api orgaos coverage.n missing the extra slice: {orgao_cov}")
    if not orgao_cov.get("methodologyVersion"):
        raise SystemExit(f"api orgaos coverage missing methodologyVersion: {orgao_cov}")

    niteroi = get_json(f"{API}/api/orgaos?municipioIbge=3303302&skip=0&take=50")
    deny_flags(niteroi, f"{API}/api/orgaos?municipioIbge=3303302")
    niteroi_rows = niteroi.get("items") or []
    if len(niteroi_rows) != 1 or str(niteroi_rows[0].get("municipioIbge") or "") != "3303302":
        raise SystemExit(f"api municipio filter 3303302 failed: {niteroi_rows}")
    bauru = get_json(f"{API}/api/orgaos?uf=SP&skip=0&take=50")
    deny_flags(bauru, f"{API}/api/orgaos?uf=SP")
    bauru_rows = bauru.get("items") or []
    if not bauru_rows or any(str(row.get("uf") or "") != "SP" for row in bauru_rows):
        raise SystemExit(f"api UF=SP filter failed: {bauru_rows}")
    if str((bauru.get("coverage") or {}).get("uf") or "") != "SP":
        raise SystemExit(f"api UF=SP coverage lost slice UF: {bauru.get('coverage')}")

    orgao = by_ibge["3306305"]
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
    if coverage.get("uf") not in (None, ""):
        raise SystemExit(f"mixed item list invented a UF: {coverage}")
    if not coverage.get("methodologyVersion"):
        raise SystemExit(f"api items coverage missing methodologyVersion: {coverage}")
    rows = items.get("items") or []
    if not rows:
        raise SystemExit("api /api/items returned no rows")
    canons = [row.get("unidadeCanonica") for row in rows]
    if all(v in (None, "") for v in canons):
        raise SystemExit("api items unidadeCanonica always null")
    base_prices = [row.get("valorPorUnidadeCanonica") for row in rows]
    if "valorPorUnidadeCanonica" not in rows[0]:
        raise SystemExit("api items missing valorPorUnidadeCanonica")
    if all(v is None for v in base_prices):
        raise SystemExit("api items valorPorUnidadeCanonica always null")
    mapped = {
        str(row.get("unidadeMedida") or "").upper(): str(row.get("unidadeCanonica") or "")
        for row in rows
    }
    if mapped.get("CX") != "cx" and mapped.get("KG") != "kg":
        raise SystemExit(f"api items missing CX/KG canonical map: {mapped}")
    unknown = [row for row in rows if str(row.get("unidadeMedida") or "").upper() == "FOOBAR"]
    if unknown and str(unknown[0].get("unidadeCanonica") or "") != "unknown":
        raise SystemExit(f"api invented a unit for FOOBAR: {unknown[0].get('unidadeCanonica')}")
    if unknown and unknown[0].get("valorPorUnidadeCanonica") is not None:
        raise SystemExit("api invented a base price for unknown unit")
    ufs = {str(row.get("uf") or "") for row in rows}
    if ufs != {"RJ", "SP"}:
        raise SystemExit(f"api items UF set is not RJ+SP: {sorted(ufs)}")
    iid = rows[0]["id"]
    item = get_json(f"{API}/api/items/{iid}")
    deny_flags(item, f"{API}/api/items/{iid}")
    deny_stub(json.dumps(item, ensure_ascii=False), "api get item")

    fornecedores = get_json(f"{API}/api/fornecedores?skip=0&take=50")
    deny_flags(fornecedores, f"{API}/api/fornecedores")
    deny_stub(json.dumps(fornecedores, ensure_ascii=False), "api /api/fornecedores")
    fornecedor_rows = fornecedores.get("items") or []
    if not fornecedor_rows:
        raise SystemExit("api /api/fornecedores returned no rows")
    fid = fornecedor_rows[0]["id"]

    contratacoes = get_json(f"{API}/api/contratacoes?skip=0&take=50")
    deny_flags(contratacoes, f"{API}/api/contratacoes")
    deny_stub(json.dumps(contratacoes, ensure_ascii=False), "api /api/contratacoes")
    contratacao_rows = contratacoes.get("items") or []
    if not contratacao_rows:
        raise SystemExit("api /api/contratacoes returned no rows")
    cid = contratacao_rows[0]["id"]

    by_fornecedor = get_json(f"{API}/api/contratacoes?skip=0&take=50&fornecedorId={fid}")
    deny_flags(by_fornecedor, f"{API}/api/contratacoes?fornecedorId")
    if not (by_fornecedor.get("items") or []):
        raise SystemExit("api /api/contratacoes?fornecedorId returned no rows")

    home = get_text(f"{WEB}/")
    assert_served_page(home, "web /")
    folded = home.casefold()
    if "volta redonda" not in folded:
        raise SystemExit("web / missing Volta Redonda")
    if "niter" not in folded:
        raise SystemExit("web / missing Niterói")
    if "bauru" not in folded:
        raise SystemExit("web / missing Bauru")
    if "UF mista" not in home:
        raise SystemExit("web / missing honest mixed UF")
    if "UF Brasil" in home or "total nacional" in folded:
        raise SystemExit("web / invented a national total")

    orgaos_html = get_text(f"{WEB}/orgaos")
    assert_served_page(orgaos_html, "web /orgaos")
    orgaos_fold = orgaos_html.casefold()
    if "volta redonda" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Volta Redonda")
    if "niter" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Niterói")
    if "bauru" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Bauru")
    if "UF mista" not in orgaos_html:
        raise SystemExit("web /orgaos missing honest mixed UF")

    niteroi_html = get_text(f"{WEB}/orgaos?municipioIbge=3303302")
    assert_served_page(niteroi_html, "web /orgaos?municipioIbge=3303302")
    niteroi_table = table_html(niteroi_html)
    if "niteroi" not in niteroi_table.casefold() and "niterói" not in niteroi_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3303302 missing Niterói")
    if "prefeitura municipal de bauru" in niteroi_table.casefold():
        raise SystemExit("web municipio filter leaked Bauru")
    if "prefeitura municipal de volta redonda" in niteroi_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", niteroi_html):
        raise SystemExit("web municipio filter missing n=1")
    if "UF RJ" not in niteroi_html:
        raise SystemExit("web municipio filter missing UF RJ")

    sp_html = get_text(f"{WEB}/orgaos?uf=SP")
    assert_served_page(sp_html, "web /orgaos?uf=SP")
    sp_table = table_html(sp_html)
    if "bauru" not in sp_table.casefold():
        raise SystemExit("web /orgaos?uf=SP missing Bauru")
    if "prefeitura municipal de volta redonda" in sp_table.casefold():
        raise SystemExit("web UF=SP filter leaked Volta Redonda")
    if "prefeitura municipal de niter" in sp_table.casefold():
        raise SystemExit("web UF=SP filter leaked Niterói")
    if "UF SP" not in sp_html:
        raise SystemExit("web UF=SP missing coverage UF")

    orgao_html = get_text(f"{WEB}/orgaos/{oid}")
    assert_served_page(orgao_html, "web /orgaos/{id}")
    if STAT_HOMOLOGADO.search(orgao_html):
        raise SystemExit("web /orgaos/{id} used Homologado as a slice total")
    if "volta redonda" not in orgao_html.casefold():
        raise SystemExit("web /orgaos/{id} missing Volta Redonda")

    fornecedor_html = get_text(f"{WEB}/fornecedores/{fid}")
    assert_served_page(fornecedor_html, "web /fornecedores/{id}")
    if STAT_HOMOLOGADO.search(fornecedor_html):
        raise SystemExit("web /fornecedores/{id} used Homologado as a slice total")

    contratacao_html = get_text(f"{WEB}/contratacoes/{cid}")
    assert_served_page(contratacao_html, "web /contratacoes/{id}")
    if not STAT_HOMOLOGADO.search(contratacao_html):
        raise SystemExit("web /contratacoes/{id} missing Homologado on the contratação")
    if not re.search(r"R\$\s*[\d.]+,\d{2}", contratacao_html):
        raise SystemExit("web /contratacoes/{id} missing money")
    if not re.search(r"\d{2}/\d{2}/\d{4}", contratacao_html):
        raise SystemExit("web /contratacoes/{id} missing date")

    item_html = get_text(f"{WEB}/itens/{iid}")
    assert_served_page(item_html, "web /itens/{id}")
    if not re.search(r"R\$\s*[\d.]+,\d{2}", item_html):
        raise SystemExit("web /itens/{id} missing money")

    empty = get_text(f"{WEB}/orgaos?q=zzzz-sem-registro")
    assert_served_page(empty, "web empty orgaos")
    if "Nenhum registro neste recorte para o filtro atual." not in empty:
        raise SystemExit("web empty orgaos missing empty copy")
    if "n=0" not in empty:
        raise SystemExit("web empty orgaos missing n=0")
    if "filtro sem registros" not in empty:
        raise SystemExit("web empty orgaos invented a UF")

    missing = get_text(f"{WEB}/orgaos/00000000-0000-0000-0000-000000000000", ok=(200, 404))
    assert_served_page(missing, "web 404")
    if "não encontrado" not in missing.casefold():
        raise SystemExit("web 404 missing not-found copy")

    cobertura = get_text(f"{WEB}/cobertura")
    assert_served_page(cobertura, "web /cobertura")
    if "3306305" not in cobertura:
        raise SystemExit("web /cobertura missing VR IBGE")
    if "3303302" not in cobertura:
        raise SystemExit("web /cobertura missing Niterói IBGE")
    if "3506003" not in cobertura:
        raise SystemExit("web /cobertura missing Bauru IBGE")
    if "não é um total nacional" not in cobertura:
        raise SystemExit("web /cobertura missing disclaimer")
    if "UF mista" not in cobertura:
        raise SystemExit("web /cobertura must stay mixed-UF")

    metodologia = get_text(f"{WEB}/metodologia")
    assert_served_page(metodologia, "web /metodologia")
    if "0.1" in metodologia and "phase1-0.1.0" not in metodologia:
        raise SystemExit("web /metodologia assumed stub methodology 0.1")

    flags = get_json(f"{API}/api/internal/flags?state=detected&skip=0&take=50")
    flag_coverage = flags.get("coverage") or {}
    flag_n = flag_coverage.get("n")
    if not isinstance(flag_n, int) or flag_n < 1:
        raise SystemExit(f"internal flags coverage.n missing or empty: {flag_coverage}")
    if not str(flag_coverage.get("methodologyVersion") or ""):
        raise SystemExit("internal flags coverage missing methodologyVersion")
    flag_rows = flags.get("items") or []
    if not flag_rows:
        raise SystemExit("internal flags returned no rows")
    kinds = {str(row.get("kind") or "") for row in flag_rows}
    if "qty_unit_price_neq_total" not in kinds:
        raise SystemExit(f"internal flags missing tier1 qty fact: {sorted(kinds)}")
    for row in flag_rows:
        if str(row.get("state") or "") != "detected":
            raise SystemExit(f"internal flag state is not detected: {row.get('state')}")
        if not row.get("itemId"):
            raise SystemExit("internal flag missing itemId")
        if not row.get("delta"):
            raise SystemExit("internal flag missing delta")
        if not row.get("snapshotId"):
            raise SystemExit("internal flag missing snapshotId")
        if not row.get("methodologyVersion"):
            raise SystemExit("internal flag missing methodologyVersion")
    paged = get_json(f"{API}/api/internal/flags?state=detected&take=1")
    if len(paged.get("items") or []) != 1:
        raise SystemExit("internal flags take=1 did not page")
    if (paged.get("coverage") or {}).get("n") != flag_n:
        raise SystemExit("internal flags page coverage.n changed")
    qty = get_json(f"{API}/api/internal/flags?kind=qty_unit_price_neq_total&state=detected")
    if not (qty.get("items") or []):
        raise SystemExit("internal flags kind filter missed qty_unit_price_neq_total")
    deny_flags(orgaos, f"{API}/api/orgaos")
    deny_flags(items, f"{API}/api/items")
    deny_flags(item, f"{API}/api/items/{iid}")

    print("compose prove ok")
    print(f"orgaos={len(items_page)} ibges={sorted(by_ibge)} items={n} flags={flag_n}")
    return 0


def assert_served_page(html: str, where: str) -> None:
    deny_stub(html, where)
    if BANNED_COPY.search(html):
        raise SystemExit(f"{where} leaked banned copy")
    if not re.search(r"n=\d+", html):
        raise SystemExit(f"{where} missing coverage n")
    if not any(token in html for token in ("UF RJ", "UF SP", "UF mista", "filtro sem registros")):
        raise SystemExit(f"{where} missing UF / empty-filter chip")
    if not re.search(r"trimestre|trim\.", html, re.I):
        raise SystemExit(f"{where} missing trimestre")
    if not re.search(r"metodologia", html, re.I):
        raise SystemExit(f"{where} missing metodologia")


def get_json(url: str) -> dict:
    raw = get_text(url)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{url} is not JSON") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{url} JSON is not an object")
    return data


def get_text(url: str, ok: tuple[int, ...] = (200,)) -> str:
    req = urllib.request.Request(url, headers={"accept": "application/json, text/html"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status not in ok:
                raise SystemExit(f"{url} status {resp.status}")
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if exc.code in ok:
            return exc.read().decode("utf-8", "replace")
        raise SystemExit(f"{url} status {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"{url} unreachable: {exc.reason}") from exc


def table_html(html: str) -> str:
    match = re.search(r"<table\b[\s\S]*?</table>", html, re.I)
    return match.group(0) if match else ""


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
