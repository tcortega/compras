from __future__ import annotations

import csv
import io
import json
import tempfile
import zipfile
from pathlib import Path

import httpx
import polars as pl

from compras_ingest.cpf import assert_no_raw_cpf, mask_frame
from compras_ingest.landing import LandingRef, LandingStore, partition_date_of
from compras_ingest.official import (
    TCE_RS_EXAMPLE_URL,
    TCE_RS_HOSTS,
    TCE_RS_LEIAUTE_URL,
    TceRsOfficial,
    download_to_retry,
    http_client,
    resolve_tce_rs_licitacon,
    tce_rs_ckan_url,
    tce_rs_portal_url,
)
from compras_ingest.settings import Settings
from compras_normalize.text import fold, parse_date

SOURCE = "tce_rs_licitacon"
# Documented live slice. Explorer does not publish this landing.
SLICE_IBGE = "4305108"
SLICE_UF = "RS"
SLICE_MUNICIPIO = "Caxias do Sul"
FIXTURE_ORGAO = "89550032000174"
TABLE_COL = "_table"

# Official leiaute 1.4 tables 9, 14, 15, 16. Open data may prefix CD_ORGAO.
LICITANTE_COLS = [
    "NR_LICITACAO",
    "ANO_LICITACAO",
    "CD_TIPO_MODALIDADE",
    "TP_DOCUMENTO_LICITANTE",
    "NR_DOCUMENTO_LICITANTE",
    "TP_DOCUMENTO_REPRES",
    "NR_DOCUMENTO_REPRES",
    "TP_CONDICAO",
    "TP_RESULTADO_HABILITACAO",
    "BL_BENEFICIO_MICRO_EPP",
]
PROPOSTA_COLS = [
    "NR_LICITACAO",
    "ANO_LICITACAO",
    "CD_TIPO_MODALIDADE",
    "TP_DOCUMENTO_LICITANTE",
    "NR_DOCUMENTO_LICITANTE",
    "DT_PROPOSTA",
    "TP_RESULTADO_PROPOSTA",
    "VL_TOTAL_PROPOSTA",
    "PC_DESCONTO",
    "VL_NOTA_TECNICA",
    "DT_HOMOLOGACAO",
    "PC_TX",
]
LOTE_PROP_COLS = [
    "NR_LICITACAO",
    "ANO_LICITACAO",
    "CD_TIPO_MODALIDADE",
    "TP_DOCUMENTO_LICITANTE",
    "NR_DOCUMENTO_LICITANTE",
    "NR_LOTE",
    "PC_DESCONTO",
    "VL_TOTAL_LOTE",
    "VL_NOTA_TECNICA",
    "DT_HOMOLOGACAO",
    "TP_RESULTADO_PROPOSTA",
    "PC_TX",
    "TP_RESULTADO_HABILITACAO",
]
ITEM_PROP_COLS = [
    "NR_LICITACAO",
    "ANO_LICITACAO",
    "CD_TIPO_MODALIDADE",
    "TP_DOCUMENTO_LICITANTE",
    "NR_DOCUMENTO_LICITANTE",
    "NR_LOTE",
    "NR_ITEM",
    "PC_BDI",
    "PC_DESCONTO",
    "PC_ENCARGOS_SOCIAIS",
    "VL_UNITARIO",
    "VL_TOTAL_ITEM",
    "VL_NOTA_TECNICA",
    "DT_HOMOLOGACAO",
    "TP_RESULTADO_PROPOSTA",
    "PC_TX",
    "TP_RESULTADO_HABILITACAO",
]
TABLE_COLS = {
    "LICITANTE": LICITANTE_COLS,
    "PROPOSTA": PROPOSTA_COLS,
    "LOTE_PROPOSTA": LOTE_PROP_COLS,
    "ITEM_PROPOSTA": ITEM_PROP_COLS,
    "LICITACAO": ["NR_LICITACAO", "ANO_LICITACAO", "CD_TIPO_MODALIDADE", "TP_DOCUMENTO_VENCEDOR", "NR_DOCUMENTO_VENCEDOR"],
    "LOTE": ["NR_LICITACAO", "ANO_LICITACAO", "CD_TIPO_MODALIDADE", "NR_LOTE", "TP_DOCUMENTO_VENCEDOR", "NR_DOCUMENTO_VENCEDOR"],
    "ITEM": ["NR_LICITACAO", "ANO_LICITACAO", "CD_TIPO_MODALIDADE", "NR_LOTE", "NR_ITEM", "TP_DOCUMENTO_VENCEDOR", "NR_DOCUMENTO_VENCEDOR"],
}
NEED_TABLES = frozenset({"LICITANTE", "PROPOSTA", "LOTE_PROPOSTA", "ITEM_PROPOSTA"})
SKIP_STEMS = (
    "pessoa",
    "comissao",
    "dotacao",
    "evento",
    "documento",
    "membro",
    "contrato",
    "cobranca",
)
_DATA_SUFFIX = {".csv", ".txt"}


def land_tce_rs_licitacon(
    settings: Settings,
    store: LandingStore | None = None,
    official: TceRsOfficial | None = None,
) -> tuple[LandingRef, pl.DataFrame]:
    store = store or LandingStore(settings)
    official = official or resolve_tce_rs_licitacon(settings.tce_rs_year, fetch=settings.tce_rs_fetch)
    _assert_official(official)
    orgao = settings.tce_rs_orgao or SLICE_IBGE
    if settings.tce_rs_fetch:
        df = _load_remote(official, orgao, filter_orgao=True)
        part = f"{official.year}-01-01"
    else:
        df = _load_fixture(settings, orgao, filter_orgao=False)
        dates = _proposta_dates(df)
        part = partition_date_of(dates) if dates else f"{official.year}-01-01"
    df = mask_frame(df)
    _assert_no_raw_cpf_frame(df)
    if df.is_empty():
        raise RuntimeError("TCE-RS LicitaCon slice produced no rows")
    tables = set(df[TABLE_COL].to_list()) if TABLE_COL in df.columns else set()
    missing = NEED_TABLES - tables
    if missing:
        raise RuntimeError(f"TCE-RS landing missing {sorted(missing)}")
    ref = store.write_parquet(SOURCE, part, df)
    meta = {
        "portal_url": official.portal_url,
        "ckan_url": official.ckan_url,
        "zip_url": official.zip_url,
        "example_url": official.example_url,
        "leiaute_url": official.leiaute_url,
        "mode": "fetch" if settings.tce_rs_fetch else "fixture",
        "via": official.via,
        "year": official.year,
        "orgao": orgao,
        "fixture_orgao": FIXTURE_ORGAO,
        "ibge": SLICE_IBGE,
        "uf": SLICE_UF,
        "municipio": SLICE_MUNICIPIO,
        "internal": True,
        "explorer": False,
        "public": False,
        "rows": ref.rows,
        "sha256": ref.sha256,
    }
    store.put(
        f"{SOURCE}/date={ref.partition_date}/{ref.sha256}.source.json",
        json.dumps(meta, indent=2).encode(),
    )
    return ref, df


def _assert_official(official: TceRsOfficial) -> None:
    if official.portal_url != tce_rs_portal_url(official.year):
        raise RuntimeError(f"TCE-RS portal URL is not official: {official.portal_url}")
    if official.ckan_url != tce_rs_ckan_url(official.year):
        raise RuntimeError(f"TCE-RS CKAN URL is not official: {official.ckan_url}")
    if official.example_url != TCE_RS_EXAMPLE_URL:
        raise RuntimeError(f"TCE-RS example remessa URL is not official: {official.example_url}")
    if official.leiaute_url != TCE_RS_LEIAUTE_URL:
        raise RuntimeError(f"TCE-RS leiaute URL is not official: {official.leiaute_url}")
    for url in (official.zip_url, official.example_url, official.ckan_url, official.leiaute_url):
        host = httpx.URL(url).host or ""
        if host not in TCE_RS_HOSTS:
            raise RuntimeError(f"refusing non-official host {host} for {url}")
    path = (httpx.URL(official.zip_url).path or "").lower()
    if "licitacoes-consolidado" not in path and "evalidador-licitacon-exemplos" not in path:
        raise RuntimeError(f"TCE-RS download is not a LicitaCon zip: {official.zip_url}")


def _load_fixture(settings: Settings, orgao: str, filter_orgao: bool) -> pl.DataFrame:
    root = _fixture_root(settings)
    if root.is_file():
        return _stream_path(root, orgao, filter_orgao)
    frames = [_stream_path(p, orgao, filter_orgao) for p in _iter_table_files(root)]
    return _concat(frames)


def _load_remote(official: TceRsOfficial, orgao: str, filter_orgao: bool) -> pl.DataFrame:
    with http_client(timeout=180.0) as client, tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        try:
            download_to_retry(client, official.zip_url, tmp, TCE_RS_HOSTS)
            return _stream_zip(Path(tmp.name), orgao, filter_orgao)
        except Exception:
            if official.zip_url == TCE_RS_EXAMPLE_URL:
                raise
            download_to_retry(client, TCE_RS_EXAMPLE_URL, tmp, TCE_RS_HOSTS)
            return _stream_zip(Path(tmp.name), orgao, filter_orgao=False)


def _fixture_root(settings: Settings) -> Path:
    path = settings.tce_rs_path
    if path is None:
        raise FileNotFoundError("TCE_RS_PATH missing and TCE_RS_FETCH is off")
    return path


def _iter_table_files(root: Path) -> list[Path]:
    files = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in {*_DATA_SUFFIX, ".zip"})
    if not files:
        raise FileNotFoundError(f"no TCE-RS csv, txt, or zip in {root}")
    return files


def _stream_path(path: Path, orgao: str, filter_orgao: bool) -> pl.DataFrame:
    if path.suffix.lower() == ".zip":
        return _stream_zip(path, orgao, filter_orgao)
    table = _table_of(path.name)
    if table is None:
        return pl.DataFrame()
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        return _read_table(fh, table, orgao, filter_orgao)


def _stream_zip(path: Path, orgao: str, filter_orgao: bool) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    with zipfile.ZipFile(path) as zf:
        names = sorted(n for n in zf.namelist() if not n.endswith("/") and _table_of(n))
        if not names:
            raise FileNotFoundError(f"TCE-RS zip has no LicitaCon tables: {path}")
        for name in names:
            table = _table_of(name)
            if table is None:
                continue
            with zf.open(name) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                frames.append(_read_table(text, table, orgao, filter_orgao))
    return _concat(frames)


def _read_table(text: io.TextIOBase, table: str, orgao: str, filter_orgao: bool) -> pl.DataFrame:
    sample = text.readline()
    if not sample:
        return _empty_table(table)
    delim = _sniff_delim(sample)
    first = next(csv.reader([sample], delimiter=delim), [])
    first = [c.lstrip("\ufeff") for c in first]
    header: list[str]
    reader = csv.reader(text, delimiter=delim)
    if _is_remessa_header(first):
        peek = next(reader, [])
        peek = [c.lstrip("\ufeff") for c in peek]
        if peek and _is_col_header(peek):
            return _rows_to_frame(table, peek, [], reader, orgao, filter_orgao)
        header = list(TABLE_COLS[table])
        leading = [peek] if peek else []
        return _rows_to_frame(table, header, leading, reader, orgao, filter_orgao)
    if _is_col_header(first):
        return _rows_to_frame(table, first, [], reader, orgao, filter_orgao)
    header = list(TABLE_COLS[table])
    return _rows_to_frame(table, header, [first], reader, orgao, filter_orgao)


def _rows_to_frame(
    table: str,
    header: list[str],
    leading: list[list[str]],
    reader,
    orgao: str,
    filter_orgao: bool,
) -> pl.DataFrame:
    header = [h.lstrip("\ufeff") for h in header]
    _require_keys(table, header)
    orgao_i = _col_index_opt(header, "cd_orgao")
    kept: list[list[str]] = []
    for row in (*leading, *reader):
        if not row or _is_remessa_header(row):
            continue
        if filter_orgao and orgao_i is not None and not _keep_orgao(row, orgao_i, orgao):
            continue
        padded = [(row[i] if i < len(row) else "") for i in range(len(header))]
        kept.append(padded)
    names = [*header, TABLE_COL]
    if not kept:
        return pl.DataFrame(schema={c: pl.String for c in names})
    body = [row + [table] for row in kept]
    return pl.DataFrame(body, schema=names, orient="row")


def _keep_orgao(row: list[str], orgao_i: int, orgao: str) -> bool:
    value = row[orgao_i] if orgao_i < len(row) else ""
    digits = "".join(c for c in str(value or "") if c.isdigit())
    want = "".join(c for c in orgao if c.isdigit())
    return digits == want or digits == SLICE_IBGE


def _require_keys(table: str, header: list[str]) -> None:
    folded = {fold(c).replace(" ", "_") for c in header}
    need = ["nr_licitacao", "ano_licitacao", "cd_tipo_modalidade"]
    if table in {"LICITANTE", "PROPOSTA", "LOTE_PROPOSTA", "ITEM_PROPOSTA"}:
        need.extend(["tp_documento_licitante", "nr_documento_licitante"])
    if table in {"LOTE", "LOTE_PROPOSTA", "ITEM", "ITEM_PROPOSTA"}:
        need.append("nr_lote")
    if table in {"ITEM", "ITEM_PROPOSTA"}:
        need.append("nr_item")
    missing = [c for c in need if c not in folded]
    if missing:
        raise RuntimeError(f"TCE-RS {table} missing {missing}")


def _is_remessa_header(fields: list[str]) -> bool:
    if len(fields) < 5:
        return False
    digits = "".join(c for c in fields[0] if c.isdigit())
    return len(digits) == 14 and "/" in fields[1]


def _is_col_header(fields: list[str]) -> bool:
    folded = {fold(c).replace(" ", "_") for c in fields}
    return "nr_licitacao" in folded or "cd_orgao" in folded


def _sniff_delim(sample: str) -> str:
    if sample.count("|") >= sample.count(";") and sample.count("|") >= sample.count(","):
        return "|"
    if sample.count(";") >= sample.count(","):
        return ";"
    return ","


def _table_of(name: str) -> str | None:
    stem = fold(Path(name).name).rsplit(".", 1)[0]
    stem = stem.replace(" ", "_").replace("-", "_")
    if any(tok in stem for tok in SKIP_STEMS):
        return None
    if "item_prop" in stem or stem.endswith("item_proposta"):
        return "ITEM_PROPOSTA"
    if "lote_prop" in stem or stem.endswith("lote_proposta"):
        return "LOTE_PROPOSTA"
    if stem == "licitante" or stem.startswith("licitante"):
        return "LICITANTE"
    if stem == "proposta" or stem.startswith("proposta"):
        return "PROPOSTA"
    if stem == "licitacao" or stem.startswith("licitacao"):
        return "LICITACAO"
    if stem == "lote" or stem.startswith("lote"):
        return "LOTE"
    if stem == "item" or stem.startswith("item"):
        return "ITEM"
    return None


def _col_index_opt(header: list[str], needle: str) -> int | None:
    want = fold(needle).replace(" ", "_")
    for i, name in enumerate(header):
        if fold(name).replace(" ", "_") == want:
            return i
    return None


def _concat(frames: list[pl.DataFrame]) -> pl.DataFrame:
    present = [f for f in frames if f.height]
    if not present:
        return pl.DataFrame(schema={TABLE_COL: pl.String})
    df = pl.concat(present, how="diagonal_relaxed")
    cols = [TABLE_COL] + sorted(c for c in df.columns if c != TABLE_COL)
    return df.select(cols)


def _empty_table(table: str) -> pl.DataFrame:
    cols = [*TABLE_COLS[table], TABLE_COL]
    return pl.DataFrame(schema={c: pl.String for c in cols})


def _proposta_dates(df: pl.DataFrame) -> list:
    col = next((c for c in df.columns if fold(c).replace(" ", "_") == "dt_proposta"), None)
    if col is None or df.is_empty():
        return []
    return [parse_date(v) for v in df[col].to_list()]


def _assert_no_raw_cpf_frame(df: pl.DataFrame) -> None:
    if df.is_empty():
        return
    blobs = [str(v) for col in df.columns for v in df[col].to_list() if v is not None]
    assert_no_raw_cpf(blobs)
