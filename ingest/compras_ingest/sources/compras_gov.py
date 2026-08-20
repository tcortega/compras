from __future__ import annotations

import codecs
import csv
import io
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import polars as pl

from compras_ingest.cpf import mask_frame
from compras_ingest.csvio import read_csv
from compras_ingest.ids import record_hash
from compras_ingest.landing import LandingRef, LandingStore, partition_date_of
from compras_ingest.official import (
    COMPRAS_GOV_HOSTS,
    USER_AGENT,
    assert_official_host,
    fixture_compras_gov_official,
)
from compras_ingest.settings import Settings
from compras_ingest.slice import keep_municipal_non_legislative, keep_slice_ibge
from compras_normalize.text import fold, parse_datetime

_IBGE_NAMES = ("unidadeorgaocodigoibge", "codibgeunidadecompradora", "municipioibge", "ibge")
_ESFERA_NAMES = ("orgaoentidadeesferaid", "esferacompradora", "esfera")
_PODER_NAMES = ("orgaoentidadepoderid", "podercomprador", "poder")
_ID_NAMES = ("idcompra",)
_ANO_NAMES = ("anocomprapncp", "ano")
_READ_CHUNK = 256 * 1024


def load_compras_gov(settings: Settings, compra_path: Path | None = None, item_path: Path | None = None) -> pl.DataFrame:
    compra_p, item_p = _resolve_paths(settings, compra_path, item_path)
    compra = mask_frame(read_csv(compra_p))
    item = mask_frame(read_csv(item_p))
    return _join(compra, item)


def land_compras_gov(settings: Settings, store: LandingStore | None = None) -> tuple[LandingRef, pl.DataFrame]:
    store = store or LandingStore(settings)
    if settings.compras_gov_fetch:
        parts = _fetch_year_frames(settings)
    else:
        parts = _fixture_year_frames(settings)
    missing = [year for year in settings.compras_gov_years if year not in parts]
    if missing:
        raise RuntimeError(
            "compras.gov.br is missing years "
            + ",".join(str(year) for year in missing)
            + "; plant rows for already-known fixture orgaos or land the official anual files"
        )
    frames: list[pl.DataFrame] = []
    last: LandingRef | None = None
    for year in sorted(parts):
        hashed = _with_record_hash(parts[year])
        dates = (
            [parse_datetime(v) for v in hashed["datapublicacaopncp"].to_list()]
            if "datapublicacaopncp" in hashed.columns
            else []
        )
        part = partition_date_of(dates, fallback=date(year, 12, 31))
        last = store.write_parquet("compras_gov", part, hashed, year=year)
        frames.append(hashed)
    if last is None:
        raise RuntimeError("compras.gov.br produced no year partitions")
    return last, pl.concat(frames, how="diagonal_relaxed")


def _fixture_year_frames(settings: Settings) -> dict[int, pl.DataFrame]:
    raw = _filter_slice(load_compras_gov(settings))
    return _split_by_year(raw, settings.compras_gov_years)


def _fetch_year_frames(settings: Settings) -> dict[int, pl.DataFrame]:
    frames: list[pl.DataFrame] = []
    with TemporaryDirectory(prefix="compras-gov-fetch-") as tmp:
        tmp_path = Path(tmp)
        for year in settings.compras_gov_years:
            official = fixture_compras_gov_official(year, settings.compras_gov_base.rstrip("/"))
            compra_f = tmp_path / f"compra-{year}.csv"
            item_f = tmp_path / f"item-{year}.csv"
            _stream_http_csv_filter(official.compra_url, compra_f, _keep_compra_row)
            keep_ids = _collect_compra_ids(compra_f)
            _stream_http_csv_filter(
                official.item_url,
                item_f,
                lambda header, row, ids=keep_ids: _keep_item_row(header, row, ids),
            )
            compra = mask_frame(read_csv(compra_f))
            item = mask_frame(read_csv(item_f))
            joined = _join(compra, item)
            if joined.height:
                frames.append(joined)
            compra_f.unlink(missing_ok=True)
            item_f.unlink(missing_ok=True)
    if not frames:
        return {}
    return _split_by_year(pl.concat(frames, how="diagonal_relaxed"), settings.compras_gov_years)


def _resolve_paths(settings: Settings, compra_path: Path | None, item_path: Path | None) -> tuple[Path, Path]:
    if compra_path and item_path:
        return compra_path, item_path
    directory = settings.compras_gov_dir
    if directory is None:
        raise FileNotFoundError("COMPRAS_GOV_DIR missing and download is not used in this slice")
    compra = _find(directory, kind="compra")
    item = _find(directory, kind="item")
    return compra, item


def _find(directory: Path, kind: str) -> Path:
    csvs = list(directory.glob("*.csv"))
    if kind == "item":
        for p in csvs:
            if "item" in p.name.lower():
                return p
    else:
        for p in csvs:
            if "compra" in p.name.lower() and "item" not in p.name.lower():
                return p
    raise FileNotFoundError(f"no {kind} CSV in {directory}")


def _join(compra: pl.DataFrame, item: pl.DataFrame) -> pl.DataFrame:
    compra_n = _lower_cols(compra)
    item_n = _lower_cols(item)
    key = "idcompra"
    if key not in compra_n.columns or key not in item_n.columns:
        raise ValueError("compras_gov CSVs need idCompra on both files")
    overlap = [c for c in compra_n.columns if c in item_n.columns and c != key]
    compra_keep = compra_n.rename({c: f"compra_{c}" for c in overlap})
    joined = item_n.join(compra_keep, on=key, how="left")
    return joined.with_columns(pl.lit("compras_gov").alias("source"))


def _with_record_hash(df: pl.DataFrame) -> pl.DataFrame:
    rec_ids = []
    hashes = []
    for row in df.iter_rows(named=True):
        folded = {fold(k).replace(" ", "").replace("_", ""): v for k, v in row.items()}
        rec = str(folded.get("idcompraitem") or f"{folded.get('idcompra')}:{folded.get('numeroitemcompra')}")
        payload = {
            k: row[k]
            for k in sorted(row)
            if fold(k) not in {"record_hash", "record_id", "source"}
        }
        rec_ids.append(rec)
        hashes.append(record_hash(payload))
    return df.with_columns(
        pl.Series("record_id", rec_ids),
        pl.Series("record_hash", hashes),
    )


def _lower_cols(df: pl.DataFrame) -> pl.DataFrame:
    return df.rename({c: fold(c).replace(" ", "").replace("_", "") for c in df.columns})


def _first_col(df: pl.DataFrame, *names: str) -> str | None:
    have = set(df.columns)
    for name in names:
        if name in have:
            return name
    return None


def _filter_slice(df: pl.DataFrame) -> pl.DataFrame:
    ibge_col = _first_col(df, *_IBGE_NAMES)
    if ibge_col is None:
        return df
    esfera_col = _first_col(df, *_ESFERA_NAMES)
    poder_col = _first_col(df, *_PODER_NAMES)
    keep = []
    for row in df.iter_rows(named=True):
        esfera = row.get(esfera_col) if esfera_col else "M"
        poder = row.get(poder_col) if poder_col else ""
        keep.append(keep_slice_ibge(row.get(ibge_col)) and keep_municipal_non_legislative(esfera, poder))
    return df.filter(pl.Series("keep", keep))


def _split_by_year(df: pl.DataFrame, years: tuple[int, ...]) -> dict[int, pl.DataFrame]:
    ano_col = _first_col(df, *_ANO_NAMES)
    if ano_col is None:
        return {}
    out: dict[int, pl.DataFrame] = {}
    token = pl.col(ano_col).cast(pl.Utf8).fill_null("").str.slice(0, 4)
    for year in years:
        part = df.filter(token == str(year))
        if part.height:
            out[year] = part
    return out


def _norm(name: str) -> str:
    return "".join(ch for ch in name.casefold() if ch.isalnum())


def _header_index_any(header: list[str], names: tuple[str, ...]) -> int | None:
    folded = [_norm(col) for col in header]
    for name in names:
        want = _norm(name)
        if want in folded:
            return folded.index(want)
    return None


def _keep_compra_row(header: list[str], row: list[str]) -> bool:
    ibge_i = _header_index_any(header, _IBGE_NAMES)
    if ibge_i is None or ibge_i >= len(row):
        return False
    if not keep_slice_ibge(row[ibge_i]):
        return False
    esfera_i = _header_index_any(header, _ESFERA_NAMES)
    poder_i = _header_index_any(header, _PODER_NAMES)
    esfera = row[esfera_i] if esfera_i is not None and esfera_i < len(row) else "M"
    poder = row[poder_i] if poder_i is not None and poder_i < len(row) else ""
    return keep_municipal_non_legislative(esfera, poder)


def _keep_item_row(header: list[str], row: list[str], keep_ids: set[str]) -> bool:
    idx = _header_index_any(header, _ID_NAMES)
    return idx is not None and idx < len(row) and row[idx] in keep_ids


def _collect_compra_ids(filtered: Path) -> set[str]:
    ids: set[str] = set()
    delim = _sniff_delim(filtered)
    with filtered.open("r", encoding="utf-8", newline="") as raw:
        reader = csv.reader(raw, delimiter=delim)
        header = next(reader, None)
        if header is None:
            return ids
        idx = _header_index_any(header, _ID_NAMES)
        if idx is None:
            return ids
        for row in reader:
            if idx < len(row) and row[idx]:
                ids.add(row[idx])
    return ids


def _sniff_delim(path: Path) -> str:
    sample = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not sample:
        return ";"
    header = sample[0]
    if header.count(";") >= header.count(","):
        return ";"
    return ","


def _stream_http_csv_filter(url: str, dest: Path, keep_row) -> None:
    assert_official_host(url, COMPRAS_GOV_HOSTS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    buf = ""
    header: list[str] | None = None
    delim = ";"
    writer = None
    with httpx.Client(
        timeout=httpx.Timeout(300.0, connect=30.0),
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        follow_redirects=True,
    ) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            assert_official_host(str(resp.url), COMPRAS_GOV_HOSTS)
            with dest.open("w", encoding="utf-8", newline="") as raw_out:
                for chunk in resp.iter_bytes(_READ_CHUNK):
                    buf += decoder.decode(chunk)
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        if line.endswith("\r"):
                            line = line[:-1]
                        if header is None:
                            delim = ";" if line.count(";") >= line.count(",") else ","
                            header = next(csv.reader(io.StringIO(line), delimiter=delim))
                            writer = csv.writer(raw_out, delimiter=delim)
                            writer.writerow(header)
                            continue
                        row = next(csv.reader(io.StringIO(line), delimiter=delim))
                        if keep_row(header, row) and writer is not None:
                            writer.writerow(row)
                tail = decoder.decode(b"", final=True)
                buf += tail
                if buf.strip() and header is not None and writer is not None:
                    row = next(csv.reader(io.StringIO(buf), delimiter=delim))
                    if keep_row(header, row):
                        writer.writerow(row)
