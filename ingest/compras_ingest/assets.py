from __future__ import annotations

from dagster import AssetExecutionContext, Definitions, asset

from compras_ingest.landing import LandingStore
from compras_ingest.pipeline import run_compras_slice
from compras_ingest.settings import Settings
from compras_ingest.sources.catalogo_cnbs import land_catalogo_cnbs
from compras_ingest.sources.compras_gov import land_compras_gov
from compras_ingest.sources.ocds import land_ocds
from compras_ingest.sources.receita_cnpj import land_receita_cnpj


def _settings() -> Settings:
    return Settings.from_env()


@asset(group_name="tier_a", description="CATMAT/CATSER from catalogo_cnbs. Needed before normalize.")
def catalogo_cnbs(context: AssetExecutionContext) -> dict:
    ref, df = land_catalogo_cnbs(_settings())
    context.log.info(f"catalogo_cnbs rows={df.height} sha={ref.sha256}")
    return ref.as_dict()


@asset(group_name="tier_a", description="Receita CNPJ dump. Download stubbed behind RECEITA_CNPJ_PATH.")
def receita_cnpj(context: AssetExecutionContext) -> dict:
    settings = _settings()
    if settings.receita_cnpj_path is None:
        context.log.warning("RECEITA_CNPJ_PATH unset. Skip download. Asset keeps landing shape.")
        return {"source": "receita_cnpj", "skipped": True}
    ref, df = land_receita_cnpj(settings)
    context.log.info(f"receita_cnpj rows={df.height} sha={ref.sha256}")
    return ref.as_dict()


@asset(group_name="tier_a", description="Compras.gov.br bulk CSVs. Primary source.")
def compras_gov(context: AssetExecutionContext) -> dict:
    ref, df = land_compras_gov(_settings())
    context.log.info(f"compras_gov rows={df.height} sha={ref.sha256}")
    return ref.as_dict()


@asset(
    group_name="tier_a",
    description="OCP OCDS feed. Schema cross-check only. Not primary.",
    deps=[compras_gov],
)
def ocds_crosscheck(context: AssetExecutionContext, compras_gov: dict) -> dict:
    _ = compras_gov
    settings = _settings()
    store = LandingStore(settings)
    compras_ids: set[str] = set()
    for key in store.list_parquet("compras_gov"):
        df = store.read_parquet(key)
        col = "numerocontrolepncp" if "numerocontrolepncp" in df.columns else None
        if col:
            compras_ids.update(str(v) for v in df[col].to_list() if v)
    if settings.ocds_path is None:
        context.log.warning("OCDS_PATH unset. Cross-check skipped.")
        return {"role": "schema_crosscheck", "primary": False, "skipped": True}
    ref, report = land_ocds(settings, compras_ids, store)
    context.log.info(f"ocds sha={ref.sha256} report={report}")
    return {**ref.as_dict(), **report}


@asset(
    group_name="warehouse",
    description="Normalize items and write Postgres entities + ClickHouse facts. Python never calls C#.",
    deps=[compras_gov, catalogo_cnbs, receita_cnpj],
)
def warehouse_entities(context: AssetExecutionContext) -> dict:
    result = run_compras_slice(_settings())
    context.log.info(f"entities={result.entity_counts} facts={result.fact_rows} flags={result.flag_rows}")
    return {
        "landing": result.landing.as_dict(),
        "entities": result.entity_counts,
        "facts": result.fact_rows,
        "flags": result.flag_rows,
        "ocds": result.ocds_report,
    }


@asset(
    group_name="detect",
    description="Tier 1 detectors. Output internal only. state=detected.",
    deps=[warehouse_entities],
)
def tier1_flags(context: AssetExecutionContext, warehouse_entities: dict) -> dict:
    context.log.info(f"tier1 flags already written by warehouse slice. n={warehouse_entities.get('flags')}")
    return {"flags": warehouse_entities.get("flags"), "state": "detected", "public": False}


defs = Definitions(
    assets=[catalogo_cnbs, receita_cnpj, compras_gov, ocds_crosscheck, warehouse_entities, tier1_flags]
)
