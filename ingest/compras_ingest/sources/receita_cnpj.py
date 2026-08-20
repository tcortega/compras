from __future__ import annotations

import csv
import io
import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from compras_ingest.cpf import assert_no_raw_cpf, is_cpf, mask_frame
from compras_ingest.csvio import read_csv
from compras_ingest.landing import LandingRef, LandingStore, partition_date_of
from compras_ingest.official import (
    RFB_HOSTS,
    RFB_SHARE_URL,
    ReceitaOfficial,
    download_to,
    http_client,
    resolve_receita_index,
)
from compras_ingest.settings import Settings
from compras_normalize.text import parse_date

# Official RFB layout. Files have no header.
EMPRESA_COLS = [
    "cnpj_basico",
    "razao_social",
    "natureza_juridica",
    "qualificacao_responsavel",
    "capital_social",
    "porte",
    "ente_federativo",
]
ESTAB_COLS = [
    "cnpj_basico",
    "cnpj_ordem",
    "cnpj_dv",
    "identificador_matriz_filial",
    "nome_fantasia",
    "situacao_cadastral",
    "data_situacao_cadastral",
    "motivo_situacao_cadastral",
    "nome_cidade_exterior",
    "pais",
    "data_inicio_atividade",
    "cnae_fiscal_principal",
    "cnae_fiscal_secundaria",
    "tipo_logradouro",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cep",
    "uf",
    "municipio",
    "ddd1",
    "telefone1",
    "ddd2",
    "telefone2",
    "ddd_fax",
    "fax",
    "correio_eletronico",
    "situacao_especial",
    "data_situacao_especial",
]
SOCIO_COLS = [
    "cnpj_basico",
    "identificador_de_socio",
    "nome_socio",
    "cnpj_cpf_do_socio",
    "qualificacao_do_socio",
    "data_entrada_sociedade",
    "pais",
    "representante_legal",
    "nome_representante",
    "qualificacao_representante",
    "faixa_etaria",
]
CNAE_COLS = ["codigo", "descricao"]
QUAL_COLS = ["codigo", "descricao"]


def land_receita_cnpj(
    settings: Settings,
    store: LandingStore | None = None,
    cnpj_basicos: set[str] | None = None,
) -> tuple[LandingRef, pl.DataFrame]:
    store = store or LandingStore(settings)
    keep = _keep_basicos(settings, cnpj_basicos)
    official: ReceitaOfficial | None = None
    if settings.receita_cnpj_fetch:
        official = resolve_receita_index()
        if not keep:
            raise ValueError("Receita remote fetch needs compras slice CNPJs or RECEITA_CNPJ_BASICOS")
        estabelecimentos, socios = _load_remote(official, keep)
        cnaes = _stream_lookup(official, "Cnaes", CNAE_COLS)
        qualificacoes = _stream_lookup(official, "Qualificacoes", QUAL_COLS)
        part = f"{official.month}-01"
    else:
        estabelecimentos, socios = _load_fixture(settings, keep)
        if settings.receita_cnpj_path is None:
            raise FileNotFoundError("RECEITA_CNPJ_PATH missing and RECEITA_CNPJ_FETCH is off")
        cnaes = _read_named(settings.receita_cnpj_path, ("Cnaes",), CNAE_COLS)
        qualificacoes = _read_named(settings.receita_cnpj_path, ("Qualificacoes",), QUAL_COLS)
        dates = [parse_date(v) for v in estabelecimentos["data_inicio_atividade"].to_list()] if (
            not estabelecimentos.is_empty() and "data_inicio_atividade" in estabelecimentos.columns
        ) else []
        part = partition_date_of(dates) if dates else datetime.now(timezone.utc).date().isoformat()
    estabelecimentos = mask_frame(estabelecimentos)
    socios = mask_frame(socios)
    cnaes = _as_str(cnaes)
    qualificacoes = _as_str(qualificacoes)
    _assert_no_raw_cpf_frame(estabelecimentos)
    _assert_no_raw_cpf_frame(socios)
    _assert_no_raw_cpf_frame(cnaes)
    _assert_no_raw_cpf_frame(qualificacoes)
    ref = store.write_parquet("receita_cnpj", part, estabelecimentos)
    socios_ref = store.write_parquet("receita_cnpj_socios", part, socios)
    cnaes_ref = store.write_parquet("receita_cnpj_cnaes", part, cnaes)
    quals_ref = store.write_parquet("receita_cnpj_qualificacoes", part, qualificacoes)
    meta = {
        "index_url": official.index_url if official else RFB_SHARE_URL,
        "mode": "fetch" if settings.receita_cnpj_fetch else "fixture",
        "month": official.month if official else part,
        "basicos_n": len(keep),
        "estabelecimentos_sha256": ref.sha256,
        "socios_sha256": socios_ref.sha256,
        "cnaes_sha256": cnaes_ref.sha256,
        "qualificacoes_sha256": quals_ref.sha256,
        "estabelecimentos_rows": ref.rows,
        "socios_rows": socios_ref.rows,
        "cnaes_rows": cnaes_ref.rows,
        "qualificacoes_rows": quals_ref.rows,
    }
    store.put(
        f"receita_cnpj/date={ref.partition_date}/{ref.sha256}.source.json",
        json.dumps(meta, indent=2).encode(),
    )
    return ref, estabelecimentos


def load_receita_cnpj(
    settings: Settings,
    cnpj_basicos: set[str] | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    keep = _keep_basicos(settings, cnpj_basicos)
    if settings.receita_cnpj_fetch:
        official = resolve_receita_index()
        if not keep:
            raise ValueError("Receita remote fetch needs compras slice CNPJs or RECEITA_CNPJ_BASICOS")
        estab, socios = _load_remote(official, keep)
    else:
        estab, socios = _load_fixture(settings, keep)
    return mask_frame(estab), mask_frame(socios)


def cnpj_basicos_from_frame(df: pl.DataFrame) -> set[str]:
    out: set[str] = set()
    if df.is_empty():
        return out
    for col in df.columns:
        name = col.lower()
        if "cnpj" not in name and name not in {"codfornecedor", "nifornecedor"}:
            continue
        for value in df[col].to_list():
            token = _alnum(value)
            if len(token) == 11 and token.isdigit():
                continue
            if len(token) >= 8:
                out.add(token[:8])
    return out


def _load_fixture(settings: Settings, keep: set[str]) -> tuple[pl.DataFrame, pl.DataFrame]:
    path = settings.receita_cnpj_path
    if path is None:
        raise FileNotFoundError("RECEITA_CNPJ_PATH missing and RECEITA_CNPJ_FETCH is off")
    empresas = _read_named(path, ("Empresas", "empresa"), EMPRESA_COLS)
    estab = _read_named(path, ("Estabelecimentos", "estabelecimento"), ESTAB_COLS)
    socios = _read_named(path, ("Socios", "socio"), SOCIO_COLS)
    _ = keep
    # Fixture CSVs are the planted set and land in full.
    return _join_filter(empresas, estab, socios, set())


def _load_remote(official: ReceitaOfficial, keep: set[str]) -> tuple[pl.DataFrame, pl.DataFrame]:
    empresas = _stream_kind(official, "Empresas", EMPRESA_COLS, keep)
    estab = _stream_kind(official, "Estabelecimentos", ESTAB_COLS, keep)
    socios = _stream_kind(official, "Socios", SOCIO_COLS, keep)
    return _join_filter(empresas, estab, socios, keep)


def _stream_lookup(official: ReceitaOfficial, prefix: str, columns: list[str]) -> pl.DataFrame:
    zips = [f for f in official.files if f.startswith(prefix) and f.endswith(".zip")]
    if not zips:
        return pl.DataFrame(schema={c: pl.String for c in columns})
    return _stream_kind(official, prefix, columns, set())


def _stream_kind(official: ReceitaOfficial, prefix: str, columns: list[str], keep: set[str]) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    zips = [f for f in official.files if f.startswith(prefix) and f.endswith(".zip")]
    if not zips:
        raise FileNotFoundError(f"RFB {official.month} has no {prefix}*.zip")
    with http_client(timeout=180.0) as client:
        for name in zips:
            url = f"{official.webdav_root}{official.month}/{name}"
            with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
                download_to(client, url, tmp, RFB_HOSTS, auth=(official.token, ""))
                frame = _filter_zip(Path(tmp.name), columns, keep)
            if frame.height:
                frames.append(frame)
    return pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame(schema={c: pl.String for c in columns})


def _filter_zip(path: Path, columns: list[str], keep: set[str]) -> pl.DataFrame:
    kept: list[list[str]] = []
    with zipfile.ZipFile(path) as zf:
        inners = [n for n in zf.namelist() if not n.endswith("/")]
        if not inners:
            raise FileNotFoundError(f"empty zip {path}")
        with zf.open(inners[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="iso-8859-1", newline="")
            reader = csv.reader(text, delimiter=";")
            for row in reader:
                if not row:
                    continue
                basico = _alnum(row[0])[:8]
                if keep and basico not in keep:
                    continue
                padded = [(row[i] if i < len(row) else "") for i in range(len(columns))]
                kept.append(padded)
    if not kept:
        return pl.DataFrame(schema={c: pl.String for c in columns})
    return pl.DataFrame(kept, schema=columns, orient="row")


def _join_filter(
    empresas: pl.DataFrame,
    estab: pl.DataFrame,
    socios: pl.DataFrame,
    keep: set[str],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    empresas = _as_str(empresas)
    estab = _as_str(estab)
    socios = _as_str(socios)
    if keep:
        empresas = empresas.filter(pl.col("cnpj_basico").map_elements(_alnum8, return_dtype=pl.String).is_in(list(keep)))
        estab = estab.filter(pl.col("cnpj_basico").map_elements(_alnum8, return_dtype=pl.String).is_in(list(keep)))
        socios = socios.filter(pl.col("cnpj_basico").map_elements(_alnum8, return_dtype=pl.String).is_in(list(keep)))
    estab = estab.with_columns(
        (
            pl.col("cnpj_basico").cast(pl.String)
            + pl.col("cnpj_ordem").cast(pl.String).str.pad_start(4, "0")
            + pl.col("cnpj_dv").cast(pl.String).str.pad_start(2, "0")
        ).alias("cnpj")
    )
    joined = estab.join(empresas, on="cnpj_basico", how="left")
    return joined, socios


def _read_named(directory: Path, tokens: tuple[str, ...], columns: list[str]) -> pl.DataFrame:
    files = list(directory.glob("*"))
    match = None
    for token in tokens:
        for p in files:
            if token.lower() in p.name.lower() and p.suffix.lower() in {".csv", ".txt"}:
                match = p
                break
        if match:
            break
    if match is None:
        raise FileNotFoundError(f"no file matching {tokens} in {directory}")
    raw = read_csv(match, separator=";", has_header=False)
    n = min(len(columns), raw.width)
    rename = {raw.columns[i]: columns[i] for i in range(n)}
    raw = raw.rename(rename)
    extra = [c for c in raw.columns if c not in columns]
    return raw.drop(extra) if extra else raw


def _keep_basicos(settings: Settings, extra: set[str] | None) -> set[str]:
    keep = {_alnum8(v) for v in (extra or set()) if _alnum8(v)}
    keep.update(_alnum8(v) for v in settings.receita_cnpj_basicos if _alnum8(v))
    return {b for b in keep if b and not (len(b) == 11 and b.isdigit() and is_cpf(b))}


def _alnum(value: object) -> str:
    return "".join(c for c in str(value or "") if c.isalnum()).upper()


def _alnum8(value: object) -> str:
    token = _alnum(value)
    return token[:8] if len(token) >= 8 else token


def _as_str(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df
    return df.with_columns([pl.col(c).cast(pl.String) for c in df.columns])


def _assert_no_raw_cpf_frame(df: pl.DataFrame) -> None:
    if df.is_empty():
        return
    blobs = [str(v) for col in df.columns for v in df[col].to_list() if v is not None]
    assert_no_raw_cpf(blobs)
