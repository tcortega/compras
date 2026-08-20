"""A3 sprint sample: Phase 0 outlier ranking plus A1+A2 after-pool.

Fixture-safe. Official ITEM is streamed. CLASSIFIER_LLM stays off.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import polars as pl

_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("ingest", "normalize", "detect"):
    _p = str(_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from compras_detect.data_error import anomaly_pool, detect_data_errors
from compras_ingest.cpf import mask_cpf
from compras_normalize.catalog import Catalog, load_catalog
from compras_normalize.classifier import QUALITY_EXACT, QUALITY_KNN, QUALITY_NONE, llm_hook_enabled
from compras_normalize.text import fold, parse_decimal, parse_datetime

COMPRA_URL = "https://repositorio.dados.gov.br/seges/comprasgov/anual/2024/comprasGOV-anual-VW_FT_PNCP_COMPRA-2024.csv"
ITEM_URL = "https://repositorio.dados.gov.br/seges/comprasgov/anual/2024/comprasGOV-anual-VW_FT_PNCP_COMPRA_ITEM-2024.csv"
CATMAT_URL = "https://repositorio.dados.gov.br/seges/comprasgov/catalogo_cnbs/catmat.csv"
CATSER_URL = "https://repositorio.dados.gov.br/seges/comprasgov/catalogo_cnbs/catser.csv"

BAURU = {
    "municipio": "Bauru",
    "ibge": "3506003",
    "uf": "SP",
    "year": 2024,
}
CAXIAS = {
    "municipio": "Caxias do Sul",
    "ibge": "4305108",
    "uf": "RS",
    "year": 2024,
}

A1_SHA = "a37b160"
A2_SHA = "15d1561"
A1_VERSION = "compras_detect.data_error"
A2_VERSION = "compras_normalize.catalog knn (CLASSIFIER_LLM off)"

PHASE0_LABELS_HEADER = "rank,id_compra,id_compra_item,ID_contratacao_PNCP,numero_item,label,evidence_url,notes"
SAMPLE_COLS = (
    "id_compra",
    "id_compra_item",
    "ID_contratacao_PNCP",
    "numero_item",
    "descricao",
    "unidade_medida",
    "quantidade",
    "valor_unitario_estimado",
    "valor_unitario_resultado",
    "valor_total",
    "valor_total_resultado",
    "evidence_url",
)
SCORE_COLS = (
    "rank",
    "id_compra",
    "id_compra_item",
    "score",
    "score_kind",
    "median",
    "mad",
    "peer_n",
    "peer_key",
    "catalog_code",
    "catalog_match",
)
LABELS = ("real", "unit error", "spec difference", "data error", "unresolved")
BLIND_BANNED = ("score", "rank", "exclusion", "reason", "median", "mad", "peer_n")

EXEC_PODER = frozenset({"e", "executivo", "1", "executive", "n", "nenhum", "naoaplicavel", "nãoaplicavel"})
LEG_PODER = frozenset({"l", "legislativo", "legislative"})
QTY_BANDS = (
    (Decimal("1"), Decimal("1"), "1"),
    (Decimal("2"), Decimal("10"), "2-10"),
    (Decimal("11"), Decimal("100"), "11-100"),
    (Decimal("101"), Decimal("1000"), "101-1000"),
)


def repo_root() -> Path:
    return _ROOT


def fixture_dir(root: Path | None = None) -> Path:
    return (root or _ROOT) / "labels" / "fixtures" / "a3"


def git_sha(root: Path | None = None) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root or _ROOT),
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _cols(df: pl.DataFrame) -> dict[str, str]:
    return {fold(c).replace(" ", "").replace("_", ""): c for c in df.columns}


def _col(df: pl.DataFrame, *names: str) -> str | None:
    folded = _cols(df)
    for name in names:
        key = fold(name).replace(" ", "").replace("_", "")
        if key in folded:
            return folded[key]
    return None


def _must_col(df: pl.DataFrame, *names: str) -> str:
    col = _col(df, *names)
    if col is None:
        raise SystemExit(f"missing column {names} in {df.columns}")
    return col


def _cell(row: dict, *names: str) -> str:
    folded = {fold(k).replace(" ", "").replace("_", ""): v for k, v in row.items()}
    for name in names:
        key = fold(name).replace(" ", "").replace("_", "")
        if key in folded and folded[key] not in (None, ""):
            return str(folded[key])
    return ""


def catalog_int(value: object) -> str:
    raw = str(value or "").strip()
    if raw == "" or raw.lower() in {"nan", "none", "null", "-"}:
        return ""
    parsed = parse_decimal(raw)
    if parsed is None or parsed <= 0:
        return ""
    return str(int(parsed))


def qty_band(qty: Decimal | None) -> str:
    if qty is None or qty <= 0:
        return ""
    if qty == Decimal("1"):
        return "1"
    for lo, hi, name in QTY_BANDS:
        if lo <= qty <= hi:
            return name
    return "1001+"


def quarter_token(value: object) -> str:
    dt = parse_datetime(value)
    if dt is None:
        return ""
    return f"{dt.year}Q{(dt.month - 1) // 3 + 1}"


def is_exec(poder: str) -> bool:
    token = fold(poder).replace(" ", "")
    if token in LEG_PODER:
        return False
    return True


def unit_price(row: dict) -> Decimal | None:
    result = parse_decimal(_cell(row, "valor_unitario_resultado"))
    if result is not None and result > 0:
        return result
    est = parse_decimal(_cell(row, "valor_unitario_estimado"))
    if est is not None and est > 0:
        return est
    return None


def qty_of(row: dict) -> Decimal | None:
    result = parse_decimal(_cell(row, "quantidade_resultado", "quantidaderesultado"))
    if result is not None and result > 0:
        return result
    return parse_decimal(_cell(row, "quantidade"))


def total_of(row: dict) -> Decimal | None:
    result = parse_decimal(_cell(row, "valor_total_resultado"))
    if result is not None:
        return result
    return parse_decimal(_cell(row, "valor_total"))


def _median(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    if n % 2:
        return ordered[n // 2]
    return (ordered[n // 2 - 1] + ordered[n // 2]) / 2


def _mad(values: list[Decimal], median: Decimal) -> Decimal:
    return _median([abs(v - median) for v in values]) or Decimal("0")


def _dec_str(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value, "f")


def read_csv(path: Path) -> pl.DataFrame:
    sample = path.read_bytes()[:4096]
    text = sample.decode("utf-8", errors="replace").splitlines()
    header = text[0] if text else ""
    if header.count(";") >= header.count(",") and header.count(";") >= header.count("\t"):
        sep = ";"
    elif header.count("\t") > header.count(","):
        sep = "\t"
    else:
        sep = ","
    return pl.read_csv(
        path,
        separator=sep,
        infer_schema_length=0,
        encoding="utf8-lossy",
        truncate_ragged_lines=True,
        try_parse_dates=False,
    )


def scan_items(path: Path, keep_ids: set[str]) -> pl.DataFrame:
    sample = path.read_bytes()[:4096]
    header = sample.decode("utf-8", errors="replace").splitlines()[0]
    sep = ";" if header.count(";") > header.count(",") else ","
    lf = pl.scan_csv(
        path,
        separator=sep,
        infer_schema_length=0,
        encoding="utf8-lossy",
        truncate_ragged_lines=True,
        try_parse_dates=False,
    )
    cols = {fold(c).replace(" ", "").replace("_", ""): c for c in lf.collect_schema().names()}
    id_col = cols.get("idcompra")
    if id_col is None:
        raise SystemExit(f"ITEM file missing id_compra: {list(cols)}")
    keep = sorted(keep_ids)
    return lf.filter(pl.col(id_col).is_in(keep)).collect()


def load_compras(path: Path) -> pl.DataFrame:
    print(f"loading COMPRA {path}", flush=True)
    return read_csv(path)


def filter_municipal(compra: pl.DataFrame, *, uf: str | None = None, ibge: str | None = None, exec_only: bool = False) -> pl.DataFrame:
    esfera = _must_col(compra, "orgao_entidade_esfera_id", "esfera")
    out = compra.filter(pl.col(esfera).str.to_uppercase() == "M")
    if uf:
        uf_col = _must_col(out, "unidade_orgao_uf_sigla", "uf")
        out = out.filter(pl.col(uf_col).str.to_uppercase() == uf.upper())
    if ibge:
        ibge_col = _must_col(out, "unidade_orgao_codigo_ibge", "municipio_ibge", "ibge")
        out = out.filter(pl.col(ibge_col).map_elements(catalog_int, return_dtype=pl.String) == ibge)
    if exec_only:
        poder = _must_col(out, "orgao_entidade_poder_id", "poder")
        out = out.filter(
            pl.col(poder).map_elements(
                lambda v: fold(str(v)).replace(" ", "") not in LEG_PODER,
                return_dtype=pl.Boolean,
            )
        )
    return out


def compra_ids(compra: pl.DataFrame) -> set[str]:
    col = _must_col(compra, "id_compra")
    return {str(v) for v in compra[col].to_list() if v not in (None, "")}


def load_catalog_sets(catmat_path: Path, catser_path: Path) -> tuple[set[str], set[str], int, int]:
    catmat = read_csv(catmat_path)
    catser = read_csv(catser_path)
    m_col = _must_col(catmat, "codigoItem", "codigo", "codigoitem")
    s_col = _must_col(catser, "codigoServico", "codigo", "codigoservico")
    mats = {catalog_int(v) for v in catmat[m_col].to_list()}
    sers = {catalog_int(v) for v in catser[s_col].to_list()}
    mats.discard("")
    sers.discard("")
    return mats, sers, catmat.height, catser.height


def catalog_frames(catmat_path: Path, catser_path: Path) -> list[pl.DataFrame]:
    catmat = read_csv(catmat_path)
    catser = read_csv(catser_path)
    m_code = _must_col(catmat, "codigoItem", "codigo", "codigoitem")
    m_desc = _must_col(catmat, "descricaoItem", "descricao", "nome")
    s_code = _must_col(catser, "codigoServico", "codigo", "codigoservico")
    s_desc = _must_col(catser, "nomeServico", "descricaoServico", "descricao", "nome")
    m = catmat.select(
        pl.col(m_code).alias("codigo"),
        pl.col(m_desc).alias("descricao"),
        pl.lit("M").alias("tipo"),
    )
    s = catser.select(
        pl.col(s_code).alias("codigo"),
        pl.col(s_desc).alias("descricao"),
        pl.lit("S").alias("tipo"),
    )
    return [m, s]


def exact_join(code: str, kind: str, catmat: set[str], catser: set[str]) -> tuple[str, str, str]:
    if not code:
        return "", "", "none"
    if kind == "S" and code in catser:
        return "", code, "catser"
    if code in catmat:
        return code, "", "catmat"
    if code in catser:
        return "", code, "catser"
    return "", "", "unmatched"


def peer_key(catalog_code: str, catalog_match: str, descricao: str) -> str:
    if catalog_code and catalog_match in {"catmat", "catser", QUALITY_EXACT, QUALITY_KNN, "knn", "exact"}:
        kind = "catser" if catalog_match in {"catser"} else "catmat"
        if catalog_match == QUALITY_KNN or catalog_match == "knn":
            kind = "knn"
        return f"{kind}:{catalog_code}"
    return f"desc:{fold(descricao)}"


def attach_item_fields(items: pl.DataFrame, compra: pl.DataFrame) -> list[dict]:
    id_c = _must_col(compra, "id_compra")
    compra_by = {str(r[id_c]): r for r in compra.iter_rows(named=True)}
    rows: list[dict] = []
    for raw in items.iter_rows(named=True):
        cid = _cell(raw, "id_compra")
        parent = compra_by.get(cid, {})
        desc = _cell(raw, "descricao_detalhada", "descricaodetalhada") or _cell(raw, "descricao")
        kind = _cell(raw, "material_ou_servico").strip().upper()[:1]
        code = catalog_int(_cell(raw, "cod_item_catalogo", "coditemcatalogo"))
        price = unit_price(raw)
        qty = qty_of(raw)
        total = total_of(raw)
        qtr = quarter_token(_cell(raw, "data_resultado") or _cell(raw, "data_inclusao") or _cell(parent, "data_publicacao_pncp", "data_inclusao"))
        pncp = _cell(raw, "ID_contratacao_PNCP", "id_contratacao_pncp", "numero_controle_PNCP") or _cell(
            parent, "numero_controle_PNCP", "ID_contratacao_PNCP"
        )
        cnpj = "".join(c for c in _cell(raw, "orgao_entidade_cnpj") or _cell(parent, "orgao_entidade_cnpj") if c.isdigit())
        ano = _cell(raw, "ano_compra") or _cell(parent, "ano_compra") or "2024"
        seq = catalog_int(_cell(raw, "sequencial_compra") or _cell(parent, "sequencial_compra"))
        item_no = catalog_int(_cell(raw, "numero_item", "numero_item_compra")) or _cell(raw, "numero_item")
        evidence = ""
        if cnpj and ano and seq:
            evidence = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{int(seq)}"
        row = {
            "id_compra": cid,
            "id_compra_item": _cell(raw, "id_compra_item"),
            "record_id": _cell(raw, "id_compra_item"),
            "ID_contratacao_PNCP": pncp,
            "pncp_id": pncp,
            "numero_item": item_no,
            "descricao": mask_cpf(desc),
            "unidade_medida": _cell(raw, "unidade_medida"),
            "quantidade": _dec_str(qty),
            "valor_unitario_estimado": _cell(raw, "valor_unitario_estimado"),
            "valor_unitario_resultado": _cell(raw, "valor_unitario_resultado"),
            "valor_unitario": _dec_str(price),
            "valor_total": _cell(raw, "valor_total"),
            "valor_total_resultado": _cell(raw, "valor_total_resultado"),
            "valor_total_num": _dec_str(total),
            "cod_item_catalogo": code,
            "material_ou_servico": kind,
            "situacao_compra_item_nome": _cell(raw, "situacao_compra_item_nome"),
            "tem_resultado": _cell(raw, "tem_resultado"),
            "orgao_cnpj": cnpj,
            "orgao_razao": mask_cpf(_cell(parent, "orgao_entidade_razao_social")),
            "poder": _cell(parent, "orgao_entidade_poder_id", "poder"),
            "esfera": _cell(parent, "orgao_entidade_esfera_id", "esfera"),
            "uf": (_cell(parent, "unidade_orgao_uf_sigla", "uf") or "").upper(),
            "municipio": _cell(parent, "unidade_orgao_municipio_nome", "municipio"),
            "ibge": catalog_int(_cell(parent, "unidade_orgao_codigo_ibge", "ibge")),
            "ano": ano,
            "sequencial": seq,
            "qty": qty,
            "price": price,
            "qty_band": qty_band(qty),
            "quarter": qtr,
            "evidence_url": evidence,
            "cod_fornecedor": mask_cpf(_cell(raw, "cod_fornecedor")),
            "nome_fornecedor": mask_cpf(_cell(raw, "nome_fornecedor")),
            "snapshot_id": "a3-2024",
            "methodology_version": "phase1-0.1.0",
        }
        rows.append(row)
    return rows


def apply_exact(rows: list[dict], catmat: set[str], catser: set[str]) -> None:
    for row in rows:
        cat_m, cat_s, match = exact_join(row["cod_item_catalogo"], row["material_ou_servico"], catmat, catser)
        row["catmat"] = cat_m
        row["catser"] = cat_s
        row["catalog_code"] = cat_m or cat_s
        row["catalog_match"] = match
        row["catmat_match_quality"] = QUALITY_EXACT if match in {"catmat", "catser"} else QUALITY_NONE
        row["peer_key"] = peer_key(row["catalog_code"], match, row["descricao"])


def apply_knn(rows: list[dict], catalog: Catalog, target_ibge: str) -> int:
    filled = 0
    for row in rows:
        if row.get("catalog_code"):
            continue
        if row.get("ibge") != target_ibge:
            continue
        hit = catalog.match(row["descricao"], None, row["material_ou_servico"])
        if not hit.assigned:
            continue
        row["catmat"] = hit.catmat or ""
        row["catser"] = hit.catser or ""
        row["catalog_code"] = hit.catmat or hit.catser or ""
        row["catalog_match"] = "knn" if hit.quality == QUALITY_KNN else "exact"
        row["catmat_match_quality"] = hit.quality
        row["peer_key"] = peer_key(row["catalog_code"], row["catalog_match"], row["descricao"])
        if hit.quality == QUALITY_KNN:
            filled += 1
    return filled


def score_rows(rows: list[dict]) -> None:
    groups: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if row["price"] is None or row["price"] <= 0:
            continue
        if not row["quarter"] or not row["qty_band"] or not row["uf"]:
            continue
        key = (row["peer_key"], row["uf"], row["quarter"], row["qty_band"])
        groups[key].append(row)
    for key, recs in groups.items():
        prices = [r["price"] for r in recs]
        med = _median(prices)
        if med is None or med <= 0:
            continue
        mad = _mad(prices, med)
        for row in recs:
            if mad == 0:
                score = row["price"] / med
                kind = "price_over_median"
            else:
                score = abs(row["price"] - med) / mad
                kind = "mad_units"
            row["median"] = med
            row["mad"] = mad
            row["score"] = score
            row["score_kind"] = kind
            row["peer_n"] = len(recs)
            row["peer_group"] = "|".join(key)


def rank_target(rows: list[dict], ibge: str, exec_only: bool = True) -> list[dict]:
    scored = []
    for row in rows:
        if row.get("ibge") != ibge:
            continue
        if exec_only and not is_exec(row.get("poder") or ""):
            continue
        if row.get("score") is None:
            continue
        scored.append(row)
    scored.sort(key=lambda r: (-float(r["score"]), str(r["id_compra_item"])))
    for i, row in enumerate(scored, start=1):
        row["rank"] = i
    return scored


def coverage_stats(rows: list[dict], ibge: str, catmat: set[str], catser: set[str], catmat_n: int, catser_n: int) -> dict:
    slice_rows = [r for r in rows if r.get("ibge") == ibge and is_exec(r.get("poder") or "")]
    n = len(slice_rows)
    n_m = 0
    n_s = 0
    n_both = 0
    n_unmatched = 0
    n_none = 0
    for row in slice_rows:
        code = row.get("cod_item_catalogo") or ""
        if not code:
            n_none += 1
            continue
        in_m = code in catmat
        in_s = code in catser
        if in_m:
            n_m += 1
        if in_s:
            n_s += 1
        if in_m and in_s:
            n_both += 1
        if not in_m and not in_s:
            n_unmatched += 1
    coded = n_m + n_s - n_both
    percent = round((coded / n) * 100, 2) if n else 0.0
    return {
        "n_items": n,
        "n_with_catmat": n_m,
        "n_with_catser": n_s,
        "n_both_catmat_and_catser": n_both,
        "n_code_present_but_unmatched": n_unmatched,
        "n_no_code": n_none,
        "n_free_text_only": n_none,
        "percent_coded": percent,
        "join_rule": "exact integer match of item.cod_item_catalogo to catmat.codigoItem or catser.codigoServico; no fuzzy description matching",
        "catalog_urls": [CATMAT_URL, CATSER_URL],
        "catmat_catalog_n": catmat_n,
        "catser_catalog_n": catser_n,
        "notes": (
            f"percent_coded = (n_with_catmat + n_with_catser - n_both) / n_items on this municipal executive slice. "
            f"Phase 0 Volta Redonda 2024 remains 81.75 percent and is not rewritten."
        ),
    }


def detect_frame(rows: list[dict]) -> pl.DataFrame:
    payload = []
    for row in rows:
        payload.append(
            {
                "record_id": row["record_id"],
                "pncp_id": row["pncp_id"],
                "descricao": row["descricao"],
                "catmat": row.get("catmat") or "",
                "catser": row.get("catser") or "",
                "quantidade": row.get("quantidade") or "",
                "valor_unitario": row.get("valor_unitario") or "",
                "valor_total": row.get("valor_total_num") or row.get("valor_total") or "",
                "snapshot_id": row.get("snapshot_id") or "",
                "methodology_version": row.get("methodology_version") or "",
            }
        )
    return pl.DataFrame(payload)


def write_csv(path: Path, rows: list[dict], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {c: row.get(c, "") for c in columns}
            writer.writerow(out)


def sample_view(row: dict) -> dict:
    return {c: row.get(c, "") for c in SAMPLE_COLS}


def score_view(row: dict) -> dict:
    return {
        "rank": row.get("rank", ""),
        "id_compra": row.get("id_compra", ""),
        "id_compra_item": row.get("id_compra_item", ""),
        "score": _dec_str(row.get("score")) if isinstance(row.get("score"), Decimal) else row.get("score", ""),
        "score_kind": row.get("score_kind", ""),
        "median": _dec_str(row.get("median")) if isinstance(row.get("median"), Decimal) else row.get("median", ""),
        "mad": _dec_str(row.get("mad")) if isinstance(row.get("mad"), Decimal) else row.get("mad", ""),
        "peer_n": row.get("peer_n", ""),
        "peer_key": row.get("peer_key", ""),
        "catalog_code": row.get("catalog_code", ""),
        "catalog_match": row.get("catalog_match", ""),
    }


def assert_blind(path: Path) -> None:
    text = path.read_text(encoding="utf-8").lower()
    header = text.splitlines()[0] if text else ""
    for banned in BLIND_BANNED:
        if banned in header.split(","):
            raise SystemExit(f"{path} header is not blind: {header}")


def choose_municipio(n_priced: int, used: dict, fallback_ok: bool) -> dict:
    if n_priced >= 100 or not fallback_ok:
        return used
    return CAXIAS


def build_manifest(
    *,
    place: dict,
    n_compras: int,
    n_items: int,
    n_priced: int,
    n_peer_items: int,
    n_before: int,
    n_after: int,
    knn_filled: int,
    sha: str,
    fixture: bool,
) -> dict:
    return {
        "municipio": place["municipio"],
        "ibge": place["ibge"],
        "uf": place["uf"],
        "year": place["year"],
        "esfera": "M",
        "poder": "municipal non-legislative (excludes L/Câmara; includes E and N as published)",
        "n_compras": n_compras,
        "n_items": n_items,
        "n_priced": n_priced,
        "n_peer_pool_items": n_peer_items,
        "n_before": n_before,
        "n_after": n_after,
        "after_fewer_than_100": n_after < 100,
        "knn_filled_target": knn_filled,
        "peer_definition": (
            "valid CATMAT/CATSER code if exact catalog join succeeded, else normalized description; "
            "plus same UF municipal 2024; plus calendar quarter; plus qty band (1 / 2-10 / 11-100 / 101-1000 / 1001+)"
        ),
        "outlier_stats": "median and MAD; score = |price-median|/MAD, or price/median if MAD==0; never mean/sigma",
        "price_field": "valor_unitario_resultado if >0 else valor_unitario_estimado",
        "before_pool": "top 100 by Phase 0 score among this municipio municipal-executive priced items",
        "after_pool": (
            "same ranking recomputed on items that remain in anomaly_pool after detect_data_errors (A1) "
            "and A2 knn fill of uncoded target descriptions; take all remaining if fewer than 100"
        ),
        "a1_version": A1_VERSION,
        "a1_sha": A1_SHA,
        "a2_version": A2_VERSION,
        "a2_sha": A2_SHA,
        "classifier_llm": False,
        "git_sha": sha,
        "official_file_urls": [COMPRA_URL, ITEM_URL, CATMAT_URL, CATSER_URL],
        "fixture": fixture,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def run_sample(
    *,
    compra_path: Path,
    item_path: Path,
    catmat_path: Path,
    catser_path: Path,
    out_dir: Path,
    place: dict,
    fallback: bool,
    knn: bool,
    fixture: bool,
) -> dict:
    if llm_hook_enabled():
        raise SystemExit("CLASSIFIER_LLM must stay off for A3")
    os.environ["CLASSIFIER_LLM"] = ""
    compra = load_compras(compra_path)
    target = filter_municipal(compra, uf=place["uf"], ibge=place["ibge"], exec_only=True)
    peer = filter_municipal(compra, uf=place["uf"])
    n_compras = target.height
    keep = compra_ids(peer)
    if not keep:
        raise SystemExit(f"no municipal COMPRA rows for UF {place['uf']}")
    print(f"streaming ITEM for {len(keep)} {place['uf']} municipal compras", flush=True)
    items = scan_items(item_path, keep)
    print(f"kept {items.height} ITEM rows", flush=True)
    catmat, catser, catmat_n, catser_n = load_catalog_sets(catmat_path, catser_path)
    rows = attach_item_fields(items, peer)
    apply_exact(rows, catmat, catser)
    target_rows = [r for r in rows if r.get("ibge") == place["ibge"] and is_exec(r.get("poder") or "")]
    n_items = len(target_rows)
    n_priced = sum(1 for r in target_rows if r.get("price") is not None and r["price"] > 0)
    if n_priced < 100 and fallback and place["ibge"] == BAURU["ibge"] and not fixture:
        print(f"Bauru priced items={n_priced} < 100; falling back to Caxias do Sul", flush=True)
        return run_sample(
            compra_path=compra_path,
            item_path=item_path,
            catmat_path=catmat_path,
            catser_path=catser_path,
            out_dir=_ROOT / "labels" / "a3-caxias-2024",
            place=CAXIAS,
            fallback=False,
            knn=knn,
            fixture=fixture,
        )
    score_rows(rows)
    before = rank_target(rows, place["ibge"])[:100]
    knn_filled = 0
    after_rows = [dict(r) for r in rows]
    if knn:
        print("loading catalog for A2 knn on uncoded target descriptions", flush=True)
        catalog = load_catalog(catalog_frames(catmat_path, catser_path))
        knn_filled = apply_knn(after_rows, catalog, place["ibge"])
        print(f"A2 knn filled {knn_filled} uncoded target rows", flush=True)
    for row in after_rows:
        if row.get("catalog_match") != "knn":
            row["peer_key"] = peer_key(row.get("catalog_code") or "", row.get("catalog_match") or "none", row["descricao"])
    exclusions = detect_data_errors(detect_frame(after_rows))
    pool = anomaly_pool(detect_frame(after_rows), exclusions)
    banned = {str(v) for v in exclusions["record_id"].to_list()} if exclusions.height else set()
    remaining = [r for r in after_rows if r["record_id"] not in banned]
    for row in remaining:
        row.pop("score", None)
        row.pop("median", None)
        row.pop("mad", None)
        row.pop("score_kind", None)
        row.pop("peer_n", None)
        row.pop("rank", None)
    score_rows(remaining)
    after = rank_target(remaining, place["ibge"])[:100]
    before_ids = {r["id_compra_item"] for r in before}
    excluded_from_before = [r for r in before if r["record_id"] in banned]
    reason_counts: dict[str, int] = Counter()
    if exclusions.height:
        for rec in exclusions.iter_rows(named=True):
            if str(rec.get("record_id") or "") in {r["record_id"] for r in excluded_from_before}:
                reason_counts[str(rec["reason"])] += 1
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "sample-before.csv", [sample_view(r) for r in before], SAMPLE_COLS)
    write_csv(out_dir / "scores-before.csv", [score_view(r) for r in before], SCORE_COLS)
    write_csv(out_dir / "scores-after.csv", [score_view(r) for r in after], SCORE_COLS)
    write_csv(
        out_dir / "peer-context.csv",
        [
            {
                "id_compra_item": r["id_compra_item"],
                "catalog_code": r.get("catalog_code", ""),
                "catalog_match": r.get("catalog_match", ""),
                "peer_key": r.get("peer_key", ""),
                "unidade_medida": r.get("unidade_medida", ""),
                "descricao": r.get("descricao", ""),
                "qty_band": r.get("qty_band", ""),
                "quarter": r.get("quarter", ""),
            }
            for r in before
        ],
        (
            "id_compra_item",
            "catalog_code",
            "catalog_match",
            "peer_key",
            "unidade_medida",
            "descricao",
            "qty_band",
            "quarter",
        ),
    )
    assert_blind(out_dir / "sample-before.csv")
    cov = coverage_stats(rows, place["ibge"], catmat, catser, catmat_n, catser_n)
    (out_dir / "catmat-coverage.json").write_text(json.dumps(cov, indent=2) + "\n", encoding="utf-8")
    manifest = build_manifest(
        place=place,
        n_compras=n_compras,
        n_items=n_items,
        n_priced=n_priced,
        n_peer_items=len(rows),
        n_before=len(before),
        n_after=len(after),
        knn_filled=knn_filled,
        sha=git_sha(),
        fixture=fixture,
    )
    manifest["n_excluded_from_before"] = len(excluded_from_before)
    manifest["exclusion_reason_counts"] = dict(reason_counts)
    manifest["before_ids"] = [r["id_compra_item"] for r in before]
    manifest["after_ids"] = [r["id_compra_item"] for r in after]
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out_dir / "exclusions-before-top100.json").write_text(
        json.dumps(
            {
                "n_excluded_from_before": len(excluded_from_before),
                "reason_counts": dict(reason_counts),
                "ids": [r["id_compra_item"] for r in excluded_from_before],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _ = before_ids
    _ = pool
    print(
        f"wrote {out_dir} municipio={place['municipio']} n_items={n_items} n_priced={n_priced} "
        f"before={len(before)} after={len(after)} excluded_from_before={len(excluded_from_before)}",
        flush=True,
    )
    return manifest


def precision_payload(labels: list[dict], *, extra: dict | None = None) -> dict:
    counts = Counter(str(r.get("label") or "") for r in labels)
    n_unresolved = counts.get("unresolved", 0)
    labeled = [r for r in labels if r.get("label") in {"real", "unit error", "spec difference", "data error"}]
    n = len(labeled)
    n_real = sum(1 for r in labeled if r["label"] == "real")
    out = {
        "n": n,
        "n_real": n_real,
        "n_unit_error": sum(1 for r in labeled if r["label"] == "unit error"),
        "n_spec_difference": sum(1 for r in labeled if r["label"] == "spec difference"),
        "n_data_error": sum(1 for r in labeled if r["label"] == "data error"),
        "n_unresolved": n_unresolved,
        "n_over_100": n_real / 100 if labels else 0.0,
        "precision_real": (n_real / n) if n else 0.0,
        "source": "labels.csv label column on this A3 sample",
        "note": "Phase 0 VR 2024 precision stays 9/100. CATMAT Phase 0 stays 81.75 percent.",
    }
    if extra:
        out.update(extra)
    return out


def read_label_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_precision(out_dir: Path) -> None:
    labels_path = out_dir / "labels.csv"
    if not labels_path.exists():
        raise SystemExit(f"missing {labels_path}")
    labels = read_label_rows(labels_path)
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    before = precision_payload(labels)
    (out_dir / "precision-before.json").write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    after_ids = list(manifest.get("after_ids") or [])
    remaining = [r for r in labels if r.get("id_compra_item") in set(after_ids)]
    labeled_after = [r for r in remaining if r.get("label") in {"real", "unit error", "spec difference", "data error"}]
    excluded = json.loads((out_dir / "exclusions-before-top100.json").read_text(encoding="utf-8"))
    n_after_unlabeled = len(after_ids) - len(remaining)
    after = precision_payload(
        remaining,
        extra={
            "n_excluded_from_before": excluded.get("n_excluded_from_before", 0),
            "exclusion_reason_counts": excluded.get("reason_counts", {}),
            "n_after_pool": len(after_ids),
            "n_after_labeled": len(labeled_after),
            "n_unresolved": n_after_unlabeled + sum(1 for r in remaining if r.get("label") == "unresolved"),
            "n_over_100": (sum(1 for r in labeled_after if r["label"] == "real") / 100) if after_ids else 0.0,
        },
    )
    (out_dir / "precision-after.json").write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")


def phase0_untouched(root: Path) -> None:
    precision = json.loads((root / "labels" / "precision.json").read_text(encoding="utf-8"))
    if precision.get("n_real") != 9 or precision.get("precision_real") != 0.09:
        raise SystemExit("Phase 0 precision.json was rewritten")
    if precision.get("n_unit_error") != 9 or precision.get("n_spec_difference") != 35 or precision.get("n_data_error") != 47:
        raise SystemExit("Phase 0 precision mix was rewritten")
    cov = json.loads((root / "labels" / "catmat-coverage.json").read_text(encoding="utf-8"))
    if cov.get("percent_coded") != 81.75:
        raise SystemExit("Phase 0 catmat-coverage.json was rewritten")
    if cov.get("n_items") != 5463:
        raise SystemExit("Phase 0 catmat n_items was rewritten")
    header = (root / "labels" / "labels.csv").read_text(encoding="utf-8").splitlines()[0]
    if header != PHASE0_LABELS_HEADER:
        raise SystemExit("Phase 0 labels.csv header was rewritten")
    first = (root / "labels" / "outliers-top100.csv").read_text(encoding="utf-8").splitlines()[1]
    if "92776105900292024" not in first:
        raise SystemExit("Phase 0 outliers-top100.csv was rewritten")


def find_a3_dir(root: Path) -> Path:
    labels = root / "labels"
    for name in ("a3-bauru-2024", "a3-caxias-2024"):
        cand = labels / name
        if (cand / "manifest.json").exists():
            return cand
    raise SystemExit("labels/a3-bauru-2024 or labels/a3-caxias-2024 missing")


def check_committed(root: Path) -> None:
    phase0_untouched(root)
    a3 = find_a3_dir(root)
    for name in (
        "manifest.json",
        "sample-before.csv",
        "scores-before.csv",
        "labels.csv",
        "labels-notes.md",
        "precision-before.json",
        "precision-after.json",
        "catmat-coverage.json",
        "README.md",
    ):
        if not (a3 / name).exists():
            raise SystemExit(f"missing {a3 / name}")
    assert_blind(a3 / "sample-before.csv")
    manifest = json.loads((a3 / "manifest.json").read_text(encoding="utf-8"))
    before = json.loads((a3 / "precision-before.json").read_text(encoding="utf-8"))
    after = json.loads((a3 / "precision-after.json").read_text(encoding="utf-8"))
    cov = json.loads((a3 / "catmat-coverage.json").read_text(encoding="utf-8"))
    labels = read_label_rows(a3 / "labels.csv")
    n = int(manifest.get("n_before") or 0)
    if n != len(labels):
        raise SystemExit(f"labels.csv has {len(labels)} rows, manifest n_before={n}")
    if n not in {100} and not manifest.get("after_fewer_than_100") and n < 100:
        raise SystemExit(f"documented n_before={n} is under 100 without a fallback note")
    mix = before["n_real"] + before["n_unit_error"] + before["n_spec_difference"] + before["n_data_error"]
    if mix != before["n"]:
        raise SystemExit("precision-before counts do not sum to n")
    mix_a = after["n_real"] + after["n_unit_error"] + after["n_spec_difference"] + after["n_data_error"]
    if mix_a != after["n"]:
        raise SystemExit("precision-after counts do not sum to n")
    if before.get("n_unresolved", 0) + before["n"] != n:
        raise SystemExit("precision-before labeled+unresolved != sample n")
    if "n_excluded_from_before" not in after:
        raise SystemExit("precision-after missing n_excluded_from_before")
    if cov.get("percent_coded") == 81.75 and cov.get("n_items") == 5463:
        raise SystemExit("A3 catmat-coverage.json copied Phase 0 VR numbers")
    if fold(str(manifest.get("municipio") or "")) == "volta redonda":
        raise SystemExit("A3 used Volta Redonda")
    sample_header = (a3 / "sample-before.csv").read_text(encoding="utf-8").splitlines()[0]
    if "score" in sample_header.split(",") or "rank" in sample_header.split(","):
        raise SystemExit("sample-before.csv is not blind")
    print(f"a3 e2e ok dir={a3.name} n={n} precision_before={before['precision_real']} precision_after={after['precision_real']}")


def run_fixture(root: Path, tmp: Path) -> None:
    fx = fixture_dir(root)
    manifest = run_sample(
        compra_path=fx / "compra.csv",
        item_path=fx / "item.csv",
        catmat_path=fx / "catmat.csv",
        catser_path=fx / "catser.csv",
        out_dir=tmp,
        place=BAURU,
        fallback=False,
        knn=True,
        fixture=True,
    )
    if not (tmp / "manifest.json").exists():
        raise SystemExit("fixture sampler did not write manifest.json")
    if int(manifest["n_before"]) < 1:
        raise SystemExit("fixture sampler wrote an empty before pool")
    assert_blind(tmp / "sample-before.csv")
    if fold(str(manifest.get("municipio") or "")) == "volta redonda":
        raise SystemExit("fixture used Volta Redonda")


def e2e_check(root: Path | None = None) -> None:
    root = root or _ROOT
    phase0_untouched(root)
    with __import__("tempfile").TemporaryDirectory() as td:
        run_fixture(root, Path(td) / "out")
    labels = root / "labels"
    if (labels / "a3-bauru-2024" / "labels.csv").exists() or (labels / "a3-caxias-2024" / "labels.csv").exists():
        check_committed(root)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="A3 Bauru/Caxias 2024 sample")
    p.add_argument("--fixture", action="store_true")
    p.add_argument("--compra", type=Path)
    p.add_argument("--item", type=Path)
    p.add_argument("--catmat", type=Path)
    p.add_argument("--catser", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--no-knn", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--precision", action="store_true", help="rebuild precision JSON from labels.csv")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        e2e_check(_ROOT)
        return 0
    if args.precision:
        out = args.out or find_a3_dir(_ROOT)
        write_precision(out)
        return 0
    if args.fixture:
        out = args.out or Path("/tmp/a3-fixture-out")
        run_fixture(_ROOT, out)
        return 0
    compra = args.compra or Path("/tmp/compras-a3/comprasGOV-anual-VW_FT_PNCP_COMPRA-2024.csv")
    item = args.item or Path("/tmp/compras-a3/comprasGOV-anual-VW_FT_PNCP_COMPRA_ITEM-2024.csv")
    catmat = args.catmat or Path("/tmp/compras-a3/catmat.csv")
    catser = args.catser or Path("/tmp/compras-a3/catser.csv")
    out = args.out or (_ROOT / "labels" / "a3-bauru-2024")
    run_sample(
        compra_path=compra,
        item_path=item,
        catmat_path=catmat,
        catser_path=catser,
        out_dir=out,
        place=BAURU,
        fallback=True,
        knn=not args.no_knn,
        fixture=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
