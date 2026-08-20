from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

METHODOLOGY_VERSION = "phase1-0.1.0"


@dataclass(frozen=True)
class Settings:
    landing_uri: str
    postgres_dsn: str
    clickhouse_url: str
    clickhouse_database: str
    clickhouse_user: str
    clickhouse_password: str
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str
    methodology_version: str
    compras_gov_dir: Path | None
    compras_gov_base: str
    compras_gov_year: int
    ocds_path: Path | None
    ocds_fetch: bool
    ocds_year: int
    catalogo_cnbs_dir: Path | None
    receita_cnpj_path: Path | None
    receita_cnpj_fetch: bool
    receita_cnpj_basicos: tuple[str, ...]
    sanctions_dir: Path | None
    pncp_consulta_dir: Path | None
    pncp_consulta_fetch: bool
    pncp_consulta_ibge: str
    pncp_consulta_year: int
    pncp_consulta_uf: str
    fixture_root: Path

    @classmethod
    def from_env(cls) -> Settings:
        root = _repo_root()
        fixture = Path(os.environ.get("COMPRAS_FIXTURE_ROOT", root / "ingest" / "fixtures"))
        return cls(
            landing_uri=os.environ.get("LANDING_URI", str(root / ".e2e-landing")),
            postgres_dsn=os.environ.get(
                "POSTGRES_DSN", "postgresql://compras:compras@127.0.0.1:5432/compras"
            ),
            clickhouse_url=os.environ.get("CLICKHOUSE_URL", "http://127.0.0.1:8123"),
            clickhouse_database=os.environ.get("CLICKHOUSE_DATABASE", "compras"),
            clickhouse_user=os.environ.get("CLICKHOUSE_USER", "compras"),
            clickhouse_password=os.environ.get("CLICKHOUSE_PASSWORD", "compras"),
            s3_endpoint=os.environ.get("AWS_ENDPOINT_URL", ""),
            s3_access_key=os.environ.get("AWS_ACCESS_KEY_ID", ""),
            s3_secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
            s3_region=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            methodology_version=os.environ.get("METHODOLOGY_VERSION", METHODOLOGY_VERSION),
            compras_gov_dir=_opt_path("COMPRAS_GOV_DIR", fixture / "compras_gov"),
            compras_gov_base=os.environ.get(
                "COMPRAS_GOV_BASE", "https://repositorio.dados.gov.br/seges/comprasgov"
            ),
            compras_gov_year=int(os.environ.get("COMPRAS_GOV_YEAR", "2024")),
            ocds_path=_opt_path("OCDS_PATH", fixture / "ocds" / "releases.jsonl"),
            ocds_fetch=_bool_env("OCDS_FETCH"),
            ocds_year=int(os.environ.get("OCDS_YEAR", os.environ.get("COMPRAS_GOV_YEAR", "2024"))),
            catalogo_cnbs_dir=_opt_path("CATALOGO_CNBS_DIR", fixture / "catalogo_cnbs"),
            receita_cnpj_path=_opt_path("RECEITA_CNPJ_PATH", fixture / "receita_cnpj"),
            receita_cnpj_fetch=_bool_env("RECEITA_CNPJ_FETCH"),
            receita_cnpj_basicos=_csv_env("RECEITA_CNPJ_BASICOS"),
            sanctions_dir=_opt_path("SANCTIONS_DIR", fixture / "sanctions"),
            pncp_consulta_dir=_opt_path("PNCP_CONSULTA_DIR", fixture / "pncp_consulta"),
            pncp_consulta_fetch=_bool_env("PNCP_CONSULTA_FETCH"),
            pncp_consulta_ibge=os.environ.get("PNCP_CONSULTA_IBGE", "3306305"),
            pncp_consulta_year=int(os.environ.get("PNCP_CONSULTA_YEAR", os.environ.get("COMPRAS_GOV_YEAR", "2024"))),
            pncp_consulta_uf=os.environ.get("PNCP_CONSULTA_UF", "RJ"),
            fixture_root=fixture,
        )


def _opt_path(key: str, default: Path) -> Path | None:
    raw = os.environ.get(key)
    path = Path(raw) if raw else default
    return path if path.exists() else None


def _bool_env(key: str) -> bool:
    return os.environ.get(key, "").strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(key: str) -> tuple[str, ...]:
    return tuple(p.strip() for p in os.environ.get(key, "").split(",") if p.strip())


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "infra" / "postgres").exists() or (p / "docs" / "CONTRACT.md").exists():
            return p
    return here.parents[2]
