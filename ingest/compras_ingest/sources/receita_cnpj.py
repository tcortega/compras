from __future__ import annotations

from pathlib import Path

import polars as pl

from compras_ingest.cpf import mask_frame
from compras_ingest.csvio import read_csv
from compras_ingest.landing import LandingRef, LandingStore
from compras_ingest.settings import Settings

# Official RFB layout. Files have no header. Download is stubbed behind RECEITA_CNPJ_PATH.
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


def load_receita_cnpj(settings: Settings) -> tuple[pl.DataFrame, pl.DataFrame]:
    path = settings.receita_cnpj_path
    if path is None:
        raise FileNotFoundError("RECEITA_CNPJ_PATH missing. CNPJ download is stubbed.")
    empresas = _read_named(path, ("Empresas", "empresa"), EMPRESA_COLS)
    estab = _read_named(path, ("Estabelecimentos", "estabelecimento"), ESTAB_COLS)
    socios = _read_named(path, ("Socios", "socio"), SOCIO_COLS)
    socios = mask_frame(socios)
    estab = estab.with_columns(
        (
            pl.col("cnpj_basico").cast(pl.String)
            + pl.col("cnpj_ordem").cast(pl.String).str.pad_start(4, "0")
            + pl.col("cnpj_dv").cast(pl.String).str.pad_start(2, "0")
        ).alias("cnpj")
    )
    joined = estab.join(empresas, on="cnpj_basico", how="left")
    return joined, socios


def land_receita_cnpj(settings: Settings, store: LandingStore | None = None) -> tuple[LandingRef, pl.DataFrame]:
    store = store or LandingStore(settings)
    estabelecimentos, socios = load_receita_cnpj(settings)
    from datetime import datetime, timezone

    part = datetime.now(timezone.utc).date().isoformat()
    ref = store.write_parquet("receita_cnpj", part, estabelecimentos)
    store.write_parquet("receita_cnpj_socios", part, socios)
    return ref, estabelecimentos


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
    return raw.rename(rename)
