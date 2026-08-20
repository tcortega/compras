from dagster import AssetExecutionContext, Definitions, asset

from compras_ingest.landing import LandingStore
from compras_ingest.pipeline import run_tier1_and_write_flags, warehouse_from_landing
from compras_ingest.settings import Settings
from compras_ingest.sources.catalogo_cnbs import land_catalogo_cnbs
from compras_ingest.sources.compras_gov import land_compras_gov
from compras_ingest.sources.ocds import land_ocds
from compras_ingest.sources.pncp_consulta import land_pncp_consulta
from compras_ingest.sources.receita_cnpj import cnpj_basicos_from_frame, land_receita_cnpj
from compras_ingest.sources.tce_rs_licitacon import land_tce_rs_licitacon
from compras_ingest.sources.tce_sp_licitacao import land_tce_sp_licitacao


def _settings() -> Settings:
    return Settings.from_env()


@asset(group_name="tier_a", description="CATMAT/CATSER from catalogo_cnbs. Needed before normalize.")
def catalogo_cnbs(context: AssetExecutionContext) -> dict:
    ref, df = land_catalogo_cnbs(_settings())
    context.log.info(f"catalogo_cnbs rows={df.height} sha={ref.sha256}")
    return ref.as_dict()


@asset(group_name="tier_a", description="Compras.gov.br bulk CSVs. Primary source.")
def compras_gov(context: AssetExecutionContext) -> dict:
    ref, df = land_compras_gov(_settings())
    context.log.info(f"compras_gov rows={df.height} sha={ref.sha256}")
    return ref.as_dict()


@asset(group_name="tier_a", description="Receita CNPJ dump. Stream-filter to compras slice. CPF masked.")
def receita_cnpj(context: AssetExecutionContext, compras_gov: dict) -> dict:
    settings = _settings()
    store = LandingStore(settings)
    basicos = _basicos_from_ref(store, compras_gov)
    ref, df = land_receita_cnpj(settings, store, cnpj_basicos=basicos)
    context.log.info(f"receita_cnpj rows={df.height} sha={ref.sha256} basicos={len(basicos)}")
    return ref.as_dict()


@asset(
    group_name="tier_a",
    description="OCP OCDS republished feed (publication 157). Schema cross-check. Not primary.",
)
def ocds_crosscheck(context: AssetExecutionContext, compras_gov: dict) -> dict:
    settings = _settings()
    store = LandingStore(settings)
    compras_ids = _compras_ids(store, compras_gov)
    ref, report = land_ocds(settings, compras_ids, store)
    context.log.info(f"ocds sha={ref.sha256} report={report}")
    return {**ref.as_dict(), **report}


@asset(
    group_name="tier_b",
    description="PNCP consulta API. Contratacoes and items. 1s spacing. Resumable. Not the Compras.gov.br bulk.",
)
def pncp_consulta(context: AssetExecutionContext) -> dict:
    ref, df, report = land_pncp_consulta(_settings())
    context.log.info(f"pncp_consulta rows={df.height} sha={ref.sha256} report={report}")
    return {**ref.as_dict(), **report}


@asset(
    group_name="tier_b",
    description="TCE-SP monthly licitacao CSV. Participant proposals. Internal only. Bauru slice. Not cubo SQL.",
)
def tce_sp_licitacao(context: AssetExecutionContext) -> dict:
    ref, df = land_tce_sp_licitacao(_settings())
    context.log.info(f"tce_sp_licitacao rows={df.height} sha={ref.sha256} public=False")
    return {**ref.as_dict(), "internal": True, "explorer": False, "public": False}


@asset(
    group_name="tier_b",
    description="TCE-RS LicitaCon participant proposals. Internal only. Caxias do Sul slice. Not public.",
)
def tce_rs_licitacon(context: AssetExecutionContext) -> dict:
    ref, df = land_tce_rs_licitacon(_settings())
    context.log.info(f"tce_rs_licitacon rows={df.height} sha={ref.sha256} public=False")
    return {**ref.as_dict(), "internal": True, "explorer": False, "public": False}


@asset(
    group_name="warehouse",
    description="Read landed parquet, normalize items, write Postgres entities and ClickHouse facts. Python never calls C#.",
)
def warehouse_entities(
    context: AssetExecutionContext,
    compras_gov: dict,
    catalogo_cnbs: dict,
    receita_cnpj: dict,
    ocds_crosscheck: dict,
    pncp_consulta: dict,
    tce_sp_licitacao: dict,
    tce_rs_licitacon: dict,
) -> dict:
    _ = ocds_crosscheck
    _ = pncp_consulta
    _ = tce_sp_licitacao
    _ = tce_rs_licitacon
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
    assets=[
        catalogo_cnbs,
        receita_cnpj,
        compras_gov,
        ocds_crosscheck,
        pncp_consulta,
        tce_sp_licitacao,
        tce_rs_licitacon,
        warehouse_entities,
        tier1_flags,
    ]
)


def required_asset_keys() -> set[str]:
    return {
        "catalogo_cnbs",
        "receita_cnpj",
        "compras_gov",
        "ocds_crosscheck",
        "pncp_consulta",
        "tce_sp_licitacao",
        "tce_rs_licitacon",
        "warehouse_entities",
        "tier1_flags",
    }


def required_warehouse_parents() -> set[str]:
    return {
        "compras_gov",
        "catalogo_cnbs",
        "receita_cnpj",
        "ocds_crosscheck",
        "pncp_consulta",
        "tce_sp_licitacao",
        "tce_rs_licitacon",
    }


def required_receita_parents() -> set[str]:
    return {"compras_gov"}


def required_ocds_parents() -> set[str]:
    return {"compras_gov"}


def required_detect_parents() -> set[str]:
    return {"warehouse_entities"}


def assert_asset_graph() -> list[str]:
    graph = defs.get_repository_def().asset_graph
    keys = [k.to_user_string() for k in graph.get_all_asset_keys()]
    missing = required_asset_keys() - set(keys)
    if missing:
        raise RuntimeError(f"dagster defs missing {missing}")
    by_name = {k.to_user_string(): k for k in graph.get_all_asset_keys()}

    def parents(name: str) -> set[str]:
        return {p.to_user_string() for p in graph.get(by_name[name]).parent_keys}

    checks = (
        ("warehouse_entities", required_warehouse_parents()),
        ("receita_cnpj", required_receita_parents()),
        ("ocds_crosscheck", required_ocds_parents()),
        ("tier1_flags", required_detect_parents()),
    )
    for name, need in checks:
        have = parents(name)
        if not need.issubset(have):
            raise RuntimeError(f"{name} missing parents {need - have}")
    return keys


def _basicos_from_ref(store: LandingStore, compras: dict) -> set[str]:
    key = compras.get("key")
    if not key:
        return set()
    return cnpj_basicos_from_frame(store.read_parquet(str(key)))


def _compras_ids(store: LandingStore, compras: dict) -> set[str]:
    key = compras.get("key")
    if not key:
        return set()
    df = store.read_parquet(str(key))
    col = "numerocontrolepncp" if "numerocontrolepncp" in df.columns else None
    if not col:
        return set()
    return {str(v) for v in df[col].to_list() if v}
