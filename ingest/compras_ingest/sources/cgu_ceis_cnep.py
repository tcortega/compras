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
    CGU_CEIS_LISTING_URL,
    CGU_CNEP_LISTING_URL,
    CGU_HOSTS,
    CguCeisCnepOfficial,
    assert_cgu_zip_url,
    download_to,
    fixture_cgu_ceis_cnep_official,
    http_client,
    resolve_cgu_ceis_cnep,
)
from compras_ingest.settings import Settings
from compras_normalize.text import fold, parse_date

SOURCE = "cgu_ceis_cnep"
NEED_FOLDED = frozenset(
    {
        "cadastro",
        "cpfoucnpjdosancionado",
        "codigodasancao",
        "datainiciosancao",
        "datafinalsancao",
    }
)


def land_cgu_ceis_cnep(
    settings: Settings,
    store: LandingStore | None = None,
    official: CguCeisCnepOfficial | None = None,
) -> tuple[LandingRef, pl.DataFrame]:
    store = store or LandingStore(settings)
    if official is None:
        if settings.sanctions_fetch:
            official = resolve_cgu_ceis_cnep()
        else:
            official = fixture_cgu_ceis_cnep_official()
    _assert_official(official)
    if settings.sanctions_fetch:
        df = _load_remote(official)
        part = official.day.isoformat()
    else:
        df = _load_fixture(settings)
        dates = _sanction_dates(df)
        part = partition_date_of(dates) if dates else official.day.isoformat()
    df = mask_frame(df)
    _assert_no_raw_cpf_frame(df)
    if df.is_empty():
        raise RuntimeError("CGU CEIS/CNEP slice produced no rows")
    cadastros = {fold(str(v)) for v in df[_col(df, "cadastro")].to_list()} if df.height else set()
    if "ceis" not in cadastros or "cnep" not in cadastros:
        raise RuntimeError(f"CGU landing missing CEIS or CNEP rows: {sorted(cadastros)}")
    ref = store.write_parquet(SOURCE, part, df)
    meta = {
        "listing_ceis": official.listing_ceis,
        "listing_cnep": official.listing_cnep,
        "ceis_download_url": official.ceis_download_url,
        "cnep_download_url": official.cnep_download_url,
        "ceis_zip_url": official.ceis_zip_url,
        "cnep_zip_url": official.cnep_zip_url,
        "mode": "fetch" if settings.sanctions_fetch else "fixture",
        "day": official.day.isoformat(),
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


def load_landed_sanctions(store: LandingStore) -> pl.DataFrame | None:
    keys = [k for k in store.list_parquet(SOURCE) if k.endswith(".parquet")]
    if not keys:
        return None
    frames = [store.read_parquet(key) for key in keys]
    frames = [f for f in frames if f is not None and not f.is_empty()]
    if not frames:
        return None
    return pl.concat(frames, how="diagonal_relaxed")


def _assert_official(official: CguCeisCnepOfficial) -> None:
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
        host = httpx.URL(url).host or ""
        if host not in CGU_HOSTS:
            raise RuntimeError(f"refusing non-official host {host} for {url}")
    assert_cgu_zip_url(official.ceis_zip_url, "ceis")
    assert_cgu_zip_url(official.cnep_zip_url, "cnep")


def _load_fixture(settings: Settings) -> pl.DataFrame:
    root = settings.sanctions_dir
    if root is None:
        raise FileNotFoundError("SANCTIONS_DIR missing and SANCTIONS_FETCH is off")
    files = _fixture_files(root)
    return _concat([_stream_path(p) for p in files])


def _load_remote(official: CguCeisCnepOfficial) -> pl.DataFrame:
    frames = [
        _stream_zip_url(official.ceis_zip_url, "ceis"),
        _stream_zip_url(official.cnep_zip_url, "cnep"),
    ]
    return _concat(frames)


def _stream_zip_url(url: str, cadastro: str) -> pl.DataFrame:
    with http_client(timeout=180.0) as client, tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        download_to(client, url, tmp, CGU_HOSTS)
        return _stream_zip(Path(tmp.name), cadastro)


def _fixture_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    files = sorted(
        p for p in root.iterdir() if p.is_file() and p.suffix.lower() in {".csv", ".zip"}
    )
    if not files:
        raise FileNotFoundError(f"no CEIS/CNEP csv or zip in {root}")
    return files


def _stream_path(path: Path) -> pl.DataFrame:
    if path.suffix.lower() == ".zip":
        return _stream_zip(path, _cadastro_from_name(path.name))
    raw = path.read_bytes()
    return _read_csv_bytes(raw, _cadastro_from_name(path.name))


def _stream_zip(path: Path, cadastro: str) -> pl.DataFrame:
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if not names:
            raise FileNotFoundError(f"CGU zip has no csv: {path}")
        frames = [_read_csv_bytes(zf.read(name), cadastro or _cadastro_from_name(name)) for name in names]
    return _concat(frames)


def _read_csv_bytes(raw: bytes, cadastro: str) -> pl.DataFrame:
    text = io.StringIO(_decode(raw), newline="")
    reader = csv.reader(text, delimiter=";")
    try:
        header = next(reader)
    except StopIteration as exc:
        raise RuntimeError("CGU CEIS/CNEP csv is empty") from exc
    header = [h.lstrip("\ufeff").strip().strip('"') for h in header]
    _require_cols(header)
    kept: list[list[str]] = []
    for row in reader:
        if not row or all(not str(c).strip() for c in row):
            continue
        padded = [(row[i] if i < len(row) else "") for i in range(len(header))]
        kept.append(padded)
    schema = {c: pl.String for c in header}
    df = pl.DataFrame(kept, schema=header, orient="row") if kept else pl.DataFrame(schema=schema)
    return _with_cadastro(df, cadastro)


def _with_cadastro(df: pl.DataFrame, cadastro: str) -> pl.DataFrame:
    if df.is_empty() and cadastro:
        return df
    col = next((c for c in df.columns if fold(c).replace(" ", "").replace("_", "") == "cadastro"), None)
    token = cadastro.strip().upper()
    if col is None and token:
        return df.with_columns(pl.lit(token).alias("CADASTRO"))
    if col is None or not token:
        return df
    return df.with_columns(
        pl.when(pl.col(col).cast(pl.String).str.strip_chars() == "")
        .then(pl.lit(token))
        .otherwise(pl.col(col))
        .alias(col)
    )


def _require_cols(header: list[str]) -> None:
    folded = {fold(c).replace(" ", "").replace("_", "") for c in header}
    aliases = {
        "cadastro": {"cadastro", "fonte"},
        "cpfoucnpjdosancionado": {"cpfoucnpjdosancionado", "cpfcnpj", "cnpj", "cpfoucnpj"},
        "codigodasancao": {"codigodasancao", "id"},
        "datainiciosancao": {"datainiciosancao", "datainicio"},
        "datafinalsancao": {"datafinalsancao", "datafimsancao", "datafim", "datafimdoefeito", "fimvigencia"},
    }
    missing = [name for name, opts in aliases.items() if name in NEED_FOLDED and not (opts & folded)]
    if missing:
        raise RuntimeError(f"CGU CEIS/CNEP csv missing {missing}")


def _cadastro_from_name(name: str) -> str:
    folded = fold(name)
    if "cnep" in folded:
        return "CNEP"
    if "ceis" in folded:
        return "CEIS"
    return ""


def _sanction_dates(df: pl.DataFrame) -> list:
    out = []
    for col in df.columns:
        key = fold(col).replace(" ", "").replace("_", "")
        if key not in {
            "datainiciosancao",
            "datainicio",
            "datafinalsancao",
            "datafimsancao",
            "datafim",
            "datafimdoefeito",
            "fimvigencia",
        }:
            continue
        out.extend(parse_date(v) for v in df[col].to_list())
    return out


def _col(df: pl.DataFrame, needle: str) -> str:
    want = fold(needle).replace(" ", "").replace("_", "")
    for col in df.columns:
        if fold(col).replace(" ", "").replace("_", "") == want:
            return col
    raise RuntimeError(f"CGU landing missing column {needle}")


def _concat(frames: list[pl.DataFrame]) -> pl.DataFrame:
    present = [f for f in frames if f is not None]
    if not present:
        return pl.DataFrame()
    return pl.concat(present, how="diagonal_relaxed")


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "iso-8859-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("iso-8859-1")


def _assert_no_raw_cpf_frame(df: pl.DataFrame) -> None:
    if df.is_empty():
        return
    blobs = [str(v) for col in df.columns for v in df[col].to_list() if v is not None]
    assert_no_raw_cpf(blobs)
