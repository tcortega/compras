from dagster import AssetExecutionContext, Definitions, asset

from compras_ingest.landing import LandingStore
from compras_ingest.pipeline import run_tier1_and_write_flags, warehouse_from_landing
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
    description="Read landed parquet, normalize items, write Postgres entities and ClickHouse facts. Python never calls C#.",
)
def warehouse_entities(
    context: AssetExecutionContext,
    compras_gov: dict,
    catalogo_cnbs: dict,
    receita_cnpj: dict,
) -> dict:
    settings = _settings()
    store = LandingStore(settings)
    items, summary = warehouse_from_landing(settings, store, compras_gov, catalogo_cnbs, receita_cnpj)
    context.log.info(
        f"normalized={items.height} entities={summary['entities']} facts={summary['facts']} items_key={summary['items_key']}"
    )
    return summary


@asset(
    group_name="detect",
    description="Run Tier 1 detectors and write internal flags. state=detected. Not public.",
)
def tier1_flags(context: AssetExecutionContext, warehouse_entities: dict) -> dict:
    settings = _settings()
    store = LandingStore(settings)
    items_key = warehouse_entities.get("items_key")
    if not items_key:
        raise RuntimeError("warehouse_entities did not persist normalized items")
    items = store.read_parquet(str(items_key))
    flags, n = run_tier1_and_write_flags(settings, store, items)
    kinds = sorted({str(v) for v in flags["kind"].to_list()}) if flags.height else []
    context.log.info(f"tier1 flags written n={n} kinds={kinds}")
    return {"flags": n, "kinds": kinds, "state": "detected", "public": False}


defs = Definitions(
    assets=[catalogo_cnbs, receita_cnpj, compras_gov, ocds_crosscheck, warehouse_entities, tier1_flags]
)


def required_asset_keys() -> set[str]:
    return {
        "catalogo_cnbs",
        "receita_cnpj",
        "compras_gov",
        "ocds_crosscheck",
        "warehouse_entities",
        "tier1_flags",
    }


def required_warehouse_parents() -> set[str]:
    return {"compras_gov", "catalogo_cnbs", "receita_cnpj"}


def required_detect_parents() -> set[str]:
    return {"warehouse_entities"}


def assert_asset_graph() -> list[str]:
    graph = defs.get_repository_def().asset_graph
    keys = [k.to_user_string() for k in graph.get_all_asset_keys()]
    missing = required_asset_keys() - set(keys)
    if missing:
        raise RuntimeError(f"dagster defs missing {missing}")
    by_name = {k.to_user_string(): k for k in graph.get_all_asset_keys()}
    warehouse_parents = {p.to_user_string() for p in graph.get(by_name["warehouse_entities"]).parent_keys}
    detect_parents = {p.to_user_string() for p in graph.get(by_name["tier1_flags"]).parent_keys}
    if not required_warehouse_parents().issubset(warehouse_parents):
        raise RuntimeError(
            f"warehouse_entities must depend on landed assets, missing {required_warehouse_parents() - warehouse_parents}"
        )
    if not required_detect_parents().issubset(detect_parents):
        raise RuntimeError(
            f"tier1_flags must depend on warehouse_entities, missing {required_detect_parents() - detect_parents}"
        )
    return keys
