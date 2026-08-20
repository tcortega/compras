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
    TCE_SP_HOSTS,
    TCE_SP_LISTING_URL,
    TceSpOfficial,
    download_to,
    fixture_tce_sp_official,
    http_client,
    resolve_tce_sp_licitacao,
)
from compras_ingest.settings import Settings
from compras_normalize.text import fold, parse_date

SOURCE = "tce_sp_licitacao"
# Documented slice. Explorer already publishes Bauru SP IBGE 3506003.
SLICE_IBGE = "3506003"
SLICE_UF = "SP"
SLICE_MUNICIPIO = "Bauru"
# Official 21 names from licitacao-2025-01_0.csv. Cubo SQL does not have these.
OFFICIAL_COLS = [
    "Município",
    "Entidade",
    "Código da Licitação",
    "Modalidade de licitação",
    "Objeto",
    "Descrição do objeto contratado",
    "Produto (item)",
    "Quantidade do objeto contratado (item)",
    "Unidade do objeto contratado",
    "Valor unitário orçamento estimativo lote",
    "Quantidade orçamento estimativo lote",
    "Unidade de medida orçamento estimativo lote",
    "Valor unitário orçamento estimativo item",
    "Quantidade orçamento estimativo item",
    "Unidade de medida orçamento estimativo item",
    "Número do edital",
    "Data do edital",
    "CNPJ do participante candidato",
    "Nome do participante candidato",
    "Resultado da Habilitação",
    "Valor da Proposta",
]


def land_tce_sp_licitacao(
    settings: Settings,
    store: LandingStore | None = None,
    official: TceSpOfficial | None = None,
) -> tuple[LandingRef, pl.DataFrame]:
    store = store or LandingStore(settings)
    if official is None:
        if settings.tce_sp_fetch:
            official = resolve_tce_sp_licitacao(settings.tce_sp_year, settings.tce_sp_month)
        else:
            official = fixture_tce_sp_official(settings.tce_sp_year, settings.tce_sp_month)
    _assert_official(official)
    municipio = settings.tce_sp_municipio or SLICE_MUNICIPIO
    if not fold(municipio):
        raise ValueError("TCE-SP ingest requires a município slice")
    if settings.tce_sp_fetch:
        df = _load_remote(official, municipio)
        part = f"{official.year}-{official.month:02d}-01"
    else:
        df = _load_fixture(settings, municipio)
        dates = _edital_dates(df)
        part = partition_date_of(dates) if dates else f"{official.year}-{official.month:02d}-01"
    df = mask_frame(df)
    _assert_no_raw_cpf_frame(df)
    if df.is_empty():
        raise RuntimeError(f"TCE-SP {municipio} slice produced no rows")
    ref = store.write_parquet(SOURCE, part, df)
    meta = {
        "listing_url": official.listing_url,
        "zip_url": official.zip_url,
        "mode": "fetch" if settings.tce_sp_fetch else "fixture",
        "year": official.year,
        "month": official.month,
        "municipio": municipio,
        "ibge": SLICE_IBGE,
        "uf": SLICE_UF,
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


def _assert_official(official: TceSpOfficial) -> None:
    if official.listing_url != TCE_SP_LISTING_URL:
        raise RuntimeError(f"TCE-SP listing URL is not official: {official.listing_url}")
    host = httpx.URL(official.zip_url).host or ""
    if host not in TCE_SP_HOSTS:
        raise RuntimeError(f"refusing non-official host {host} for {official.zip_url}")
    if "/licitacoes-contratos/licitacao-" not in official.zip_url:
        raise RuntimeError(f"TCE-SP download is not a licitacao zip: {official.zip_url}")
    if "cubo" in official.zip_url.lower():
        raise RuntimeError(f"TCE-SP cubo SQL is not the licitacao extract: {official.zip_url}")


def _load_fixture(settings: Settings, municipio: str) -> pl.DataFrame:
    path = _fixture_file(settings)
    return _stream_path(path, municipio)


def _load_remote(official: TceSpOfficial, municipio: str) -> pl.DataFrame:
    with http_client(timeout=180.0) as client, tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        download_to(client, official.zip_url, tmp, TCE_SP_HOSTS)
        return _stream_zip(Path(tmp.name), municipio)


def _fixture_file(settings: Settings) -> Path:
    path = settings.tce_sp_path
    if path is None:
        raise FileNotFoundError("TCE_SP_PATH missing and TCE_SP_FETCH is off")
    if path.is_file():
        return path
    files = sorted(p for p in path.iterdir() if p.suffix.lower() in {".csv", ".zip"} and p.is_file())
    if not files:
        raise FileNotFoundError(f"no TCE-SP csv or zip in {path}")
    return files[0]


def _stream_path(path: Path, municipio: str) -> pl.DataFrame:
    if path.suffix.lower() == ".zip":
        return _stream_zip(path, municipio)
    with path.open("r", encoding="utf-8", newline="") as fh:
        return _read_filtered(fh, municipio)


def _stream_zip(path: Path, municipio: str) -> pl.DataFrame:
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if not names:
            raise FileNotFoundError(f"TCE-SP zip has no csv: {path}")
        with zf.open(names[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            return _read_filtered(text, municipio)


def _read_filtered(text: io.TextIOBase, municipio: str) -> pl.DataFrame:
    reader = csv.reader(text, delimiter=";")
    try:
        header = next(reader)
    except StopIteration as exc:
        raise RuntimeError("TCE-SP csv is empty") from exc
    header = [h.lstrip("\ufeff") for h in header]
    _require_cols(header)
    mun_i = _col_index(header, "municipio")
    want = fold(municipio)
    kept: list[list[str]] = []
    for row in reader:
        if not row:
            continue
        value = row[mun_i] if mun_i < len(row) else ""
        if not _keep_municipio(value, want):
            continue
        padded = [(row[i] if i < len(row) else "") for i in range(len(header))]
        kept.append(padded)
    schema = {c: pl.String for c in header}
    if not kept:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame(kept, schema=header, orient="row")


def _keep_municipio(value: str, want: str) -> bool:
    if fold(value) == want:
        return True
    digits = "".join(c for c in str(value or "") if c.isdigit())
    return digits == SLICE_IBGE


def _require_cols(header: list[str]) -> None:
    folded = {fold(c) for c in header}
    missing = [c for c in OFFICIAL_COLS if fold(c) not in folded]
    if missing:
        raise RuntimeError(f"TCE-SP csv missing {missing}")


def _col_index(header: list[str], needle: str) -> int:
    for i, name in enumerate(header):
        if fold(name) == fold(needle):
            return i
    raise RuntimeError(f"TCE-SP csv missing column {needle}")


def _edital_dates(df: pl.DataFrame) -> list:
    col = next((c for c in df.columns if fold(c) == fold("Data do edital")), None)
    if col is None or df.is_empty():
        return []
    return [parse_date(v) for v in df[col].to_list()]


def _assert_no_raw_cpf_frame(df: pl.DataFrame) -> None:
    if df.is_empty():
        return
    blobs = [str(v) for col in df.columns for v in df[col].to_list() if v is not None]
    assert_no_raw_cpf(blobs)
