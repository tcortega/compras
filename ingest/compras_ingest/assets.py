from dagster import AssetExecutionContext, Definitions, ScheduleDefinition, asset, define_asset_job

from compras_ingest.incremental import (
    DAILY_ASSET_KEYS,
    DAILY_CGU_REASON,
    DAILY_COMPRAS_GOV_REASON,
    DAILY_CRON,
    DAILY_JOB_NAME,
    DAILY_OCDS_REASON,
    DAILY_PNCP_REASON,
    DAILY_SCHEDULE_NAME,
    DAILY_TCE_RS_REASON,
    MONTHLY_ASSET_KEYS,
    MONTHLY_CATALOGO_REASON,
    MONTHLY_CRON,
    MONTHLY_JOB_NAME,
    MONTHLY_RECEITA_REASON,
    MONTHLY_SCHEDULE_NAME,
    MONTHLY_TCE_SP_REASON,
    SCHEDULE_TZ as INCREMENTAL_TZ,
)
from compras_ingest.landing import LandingStore
from compras_ingest.pipeline import (
    run_adjacency_and_write,
    run_pncp_consulta_gaps,
    run_tier1_and_write_flags,
    warehouse_from_landing,
)
from compras_ingest.pncp_ids import live_ibge_targets
from compras_ingest.refetch import (
    JOB_NAME,
    REFETCH_SOURCES,
    SCHEDULE_CRON,
    SCHEDULE_NAME,
    SCHEDULE_TZ,
    refetch_source,
    trailing_window,
    trailing_window_days,
)
from compras_ingest.settings import Settings
from compras_ingest.sources.catalogo_cnbs import land_catalogo_cnbs
from compras_ingest.sources.compras_gov import land_compras_gov
from compras_ingest.sources.ocds import land_ocds
from compras_ingest.sources.pncp_consulta import GAPS_CURSOR_KEY, land_pncp_consulta
from compras_ingest.sources.cgu_ceis_cnep import land_cgu_ceis_cnep
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


GAPS_JOB_NAME = "pncp_consulta_gaps_run"
GAPS_SCHEDULE_NAME = "pncp_consulta_gaps_daily"
GAPS_SCHEDULE_CRON = "30 4 * * *"
GAPS_SCHEDULE_TZ = "America/Sao_Paulo"
GAPS_ASSET_NAME = "pncp_consulta_gaps"


@asset(
    name=GAPS_ASSET_NAME,
    group_name="tier_b",
    description="PNCP consulta gaps for the covered 59. Skip complete compras.gov rows. 1s spacing. America/Sao_Paulo.",
)
def pncp_consulta_gaps(context: AssetExecutionContext) -> dict:
    settings = _settings()
    store = LandingStore(settings)
    ref, df, report = run_pncp_consulta_gaps(settings, store)
    context.log.info(
        f"pncp_consulta_gaps rows={df.height} sha={ref.sha256} "
        f"targets={len(live_ibge_targets())} cursor={GAPS_CURSOR_KEY} report={report}"
    )
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
    group_name="tier_b",
    description="CGU CEIS and CNEP bulk CSVs. Award-window join. Internal only. Not public.",
)
def cgu_ceis_cnep(context: AssetExecutionContext) -> dict:
    ref, df = land_cgu_ceis_cnep(_settings())
    context.log.info(f"cgu_ceis_cnep rows={df.height} sha={ref.sha256} public=False")
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
    cgu_ceis_cnep: dict,
) -> dict:
    _ = ocds_crosscheck
    _ = tce_sp_licitacao
    _ = tce_rs_licitacon
    _ = cgu_ceis_cnep
    settings = _settings()
    store = LandingStore(settings)
    items, summary = warehouse_from_landing(
        settings, store, compras_gov, catalogo_cnbs, receita_cnpj, pncp_consulta
    )
    context.log.info(
        f"normalized={items.height} entities={summary['entities']} facts={summary['facts']} exclusions={summary.get('exclusions')} pool={summary.get('anomaly_pool_n')} items_key={summary['items_key']}"
    )
    return summary


@asset(
    group_name="detect",
    description="Receita shared-partner, address, phone, and email edges. Internal only. Not a finding.",
)
def fornecedor_adjacency(context: AssetExecutionContext, warehouse_entities: dict) -> dict:
    settings = _settings()
    store = LandingStore(settings)
    _ = warehouse_entities
    edges, n = run_adjacency_and_write(settings, store)
    kinds = sorted({str(v) for v in edges["kind"].to_list()}) if edges.height else []
    context.log.info(f"fornecedor_adjacency written n={n} kinds={kinds} public=False")
    return {"edges": n, "kinds": kinds, "public": False, "internal": True}


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


def _refetch_asset(source: str):
    @asset(
        name=f"refetch_{source}",
        group_name="refetch",
        description=f"Trailing-window re-fetch of {source}. Write-once content hash. Fixture mode stays local.",
    )
    def _asset(context: AssetExecutionContext) -> dict:
        settings = _settings()
        window = trailing_window(settings)
        ref = refetch_source(settings, source, window=window)
        context.log.info(
            f"refetch {source} days={trailing_window_days(settings)} "
            f"window={window[0].isoformat()}/{window[1].isoformat()} sha={ref.sha256}"
        )
        return {
            **ref.as_dict(),
            "trailing_window_days": trailing_window_days(settings),
            "window_start": window[0].isoformat(),
            "window_end": window[1].isoformat(),
        }

    return _asset


refetch_compras_gov = _refetch_asset("compras_gov")
refetch_pncp_consulta = _refetch_asset("pncp_consulta")
refetch_tce_sp_licitacao = _refetch_asset("tce_sp_licitacao")
refetch_tce_rs_licitacon = _refetch_asset("tce_rs_licitacon")
refetch_cgu_ceis_cnep = _refetch_asset("cgu_ceis_cnep")

REFETCH_ASSETS = [
    refetch_compras_gov,
    refetch_pncp_consulta,
    refetch_tce_sp_licitacao,
    refetch_tce_rs_licitacon,
    refetch_cgu_ceis_cnep,
]

trailing_window_refetch_job = define_asset_job(
    name=JOB_NAME,
    selection=[f"refetch_{source}" for source in REFETCH_SOURCES],
    description="Daily trailing-window re-fetch of landed sources.",
)

trailing_window_refetch_schedule = ScheduleDefinition(
    name=SCHEDULE_NAME,
    job=trailing_window_refetch_job,
    cron_schedule=SCHEDULE_CRON,
    execution_timezone=SCHEDULE_TZ,
)

pncp_consulta_gaps_job = define_asset_job(
    name=GAPS_JOB_NAME,
    selection=[GAPS_ASSET_NAME],
    description="Daily PNCP consulta gaps for the covered 59 municipios.",
)

pncp_consulta_gaps_schedule = ScheduleDefinition(
    name=GAPS_SCHEDULE_NAME,
    job=pncp_consulta_gaps_job,
    cron_schedule=GAPS_SCHEDULE_CRON,
    execution_timezone=GAPS_SCHEDULE_TZ,
)

incremental_land_daily_job = define_asset_job(
    name=DAILY_JOB_NAME,
    selection=list(DAILY_ASSET_KEYS),
    description=(
        f"Daily incremental land. compras_gov: {DAILY_COMPRAS_GOV_REASON}. "
        f"ocds: {DAILY_OCDS_REASON}. pncp_consulta: {DAILY_PNCP_REASON}. "
        f"tce_rs: {DAILY_TCE_RS_REASON}. cgu: {DAILY_CGU_REASON}."
    ),
)

incremental_land_monthly_job = define_asset_job(
    name=MONTHLY_JOB_NAME,
    selection=list(MONTHLY_ASSET_KEYS),
    description=(
        f"Monthly incremental land. catalogo_cnbs: {MONTHLY_CATALOGO_REASON}. "
        f"receita_cnpj: {MONTHLY_RECEITA_REASON}. tce_sp: {MONTHLY_TCE_SP_REASON}."
    ),
)

incremental_land_daily_schedule = ScheduleDefinition(
    name=DAILY_SCHEDULE_NAME,
    job=incremental_land_daily_job,
    cron_schedule=DAILY_CRON,
    execution_timezone=INCREMENTAL_TZ,
)

incremental_land_monthly_schedule = ScheduleDefinition(
    name=MONTHLY_SCHEDULE_NAME,
    job=incremental_land_monthly_job,
    cron_schedule=MONTHLY_CRON,
    execution_timezone=INCREMENTAL_TZ,
)

defs = Definitions(
    assets=[
        catalogo_cnbs,
        receita_cnpj,
        compras_gov,
        ocds_crosscheck,
        pncp_consulta,
        pncp_consulta_gaps,
        tce_sp_licitacao,
        tce_rs_licitacon,
        cgu_ceis_cnep,
        warehouse_entities,
        fornecedor_adjacency,
        tier1_flags,
        *REFETCH_ASSETS,
    ],
    jobs=[
        trailing_window_refetch_job,
        pncp_consulta_gaps_job,
        incremental_land_daily_job,
        incremental_land_monthly_job,
    ],
    schedules=[
        trailing_window_refetch_schedule,
        pncp_consulta_gaps_schedule,
        incremental_land_daily_schedule,
        incremental_land_monthly_schedule,
    ],
)


def required_asset_keys() -> set[str]:
    return {
        "catalogo_cnbs",
        "receita_cnpj",
        "compras_gov",
        "ocds_crosscheck",
        "pncp_consulta",
        GAPS_ASSET_NAME,
        "tce_sp_licitacao",
        "tce_rs_licitacon",
        "cgu_ceis_cnep",
        "warehouse_entities",
        "fornecedor_adjacency",
        "tier1_flags",
        *required_refetch_asset_keys(),
    }


def required_refetch_asset_keys() -> set[str]:
    return {f"refetch_{source}" for source in REFETCH_SOURCES}


def required_warehouse_parents() -> set[str]:
    return {
        "compras_gov",
        "catalogo_cnbs",
        "receita_cnpj",
        "ocds_crosscheck",
        "pncp_consulta",
        "tce_sp_licitacao",
        "tce_rs_licitacon",
        "cgu_ceis_cnep",
    }


def required_receita_parents() -> set[str]:
    return {"compras_gov"}


def required_ocds_parents() -> set[str]:
    return {"compras_gov"}


def required_gaps_parents() -> set[str]:
    return set()


def required_detect_parents() -> set[str]:
    return {"warehouse_entities"}


def required_adjacency_parents() -> set[str]:
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
        ("fornecedor_adjacency", required_adjacency_parents()),
        (GAPS_ASSET_NAME, required_gaps_parents()),
    )
    for name, need in checks:
        have = parents(name)
        if not need.issubset(have):
            raise RuntimeError(f"{name} missing parents {need - have}")
        if name == GAPS_ASSET_NAME and have:
            raise RuntimeError(f"{name} must not rematerialize upstream {have}")
    assert_refetch_schedule()
    assert_gaps_schedule()
    assert_incremental_schedules()
    return keys


def assert_refetch_schedule() -> None:
    schedules = list(defs.schedules or [])
    found = next((s for s in schedules if s.name == SCHEDULE_NAME), None)
    if found is None:
        raise RuntimeError(f"dagster defs missing schedule {SCHEDULE_NAME}")
    if not found.cron_schedule:
        raise RuntimeError("trailing-window refetch schedule missing cron")
    if found.execution_timezone != SCHEDULE_TZ:
        raise RuntimeError(f"refetch schedule tz is {found.execution_timezone} not {SCHEDULE_TZ}")
    target = found.job_name or getattr(found.job, "name", "")
    if target != JOB_NAME:
        raise RuntimeError(f"schedule does not target {JOB_NAME}: {target}")
    job = defs.resolve_job_def(JOB_NAME)
    selected = _job_asset_keys(job)
    need = required_refetch_asset_keys()
    if not selected:
        raise RuntimeError(f"{JOB_NAME} has no asset selection")
    if not need.issubset(selected):
        raise RuntimeError(f"{JOB_NAME} missing refetch assets {need - selected}")


def assert_gaps_schedule() -> None:
    if GAPS_SCHEDULE_TZ != "America/Sao_Paulo":
        raise RuntimeError(f"PNCP gaps tz is {GAPS_SCHEDULE_TZ}")
    schedules = list(defs.schedules or [])
    found = next((s for s in schedules if s.name == GAPS_SCHEDULE_NAME), None)
    if found is None:
        raise RuntimeError(f"dagster defs missing schedule {GAPS_SCHEDULE_NAME}")
    if not found.cron_schedule:
        raise RuntimeError("PNCP gaps schedule missing cron")
    if found.execution_timezone != GAPS_SCHEDULE_TZ:
        raise RuntimeError(f"PNCP gaps tz is {found.execution_timezone} not {GAPS_SCHEDULE_TZ}")
    target = found.job_name or getattr(found.job, "name", "")
    if target != GAPS_JOB_NAME:
        raise RuntimeError(f"gaps schedule does not target {GAPS_JOB_NAME}: {target}")
    job = defs.resolve_job_def(GAPS_JOB_NAME)
    selected = _job_asset_keys(job)
    if selected and GAPS_ASSET_NAME not in selected:
        raise RuntimeError(f"{GAPS_JOB_NAME} missing {GAPS_ASSET_NAME}")


def assert_incremental_schedules() -> None:
    _assert_one_incremental_schedule(
        DAILY_SCHEDULE_NAME,
        DAILY_JOB_NAME,
        DAILY_CRON,
        INCREMENTAL_TZ,
        set(DAILY_ASSET_KEYS),
    )
    _assert_one_incremental_schedule(
        MONTHLY_SCHEDULE_NAME,
        MONTHLY_JOB_NAME,
        MONTHLY_CRON,
        INCREMENTAL_TZ,
        set(MONTHLY_ASSET_KEYS),
    )


def _assert_one_incremental_schedule(
    schedule_name: str,
    job_name: str,
    cron: str,
    tz: str,
    need: set[str],
) -> None:
    schedules = list(defs.schedules or [])
    found = next((s for s in schedules if s.name == schedule_name), None)
    if found is None:
        raise RuntimeError(f"dagster defs missing schedule {schedule_name}")
    if not found.cron_schedule:
        raise RuntimeError(f"{schedule_name} missing cron")
    if found.cron_schedule != cron:
        raise RuntimeError(f"{schedule_name} cron {found.cron_schedule} != {cron}")
    if found.execution_timezone != tz:
        raise RuntimeError(f"{schedule_name} tz is {found.execution_timezone} not {tz}")
    target = found.job_name or getattr(found.job, "name", "")
    if target != job_name:
        raise RuntimeError(f"{schedule_name} does not target {job_name}: {target}")
    job = defs.resolve_job_def(job_name)
    selected = _job_asset_keys(job)
    if not selected:
        raise RuntimeError(f"{job_name} has no asset selection")
    if not need.issubset(selected):
        raise RuntimeError(f"{job_name} missing land assets {need - selected}")


def _job_asset_keys(job) -> set[str]:
    layer = getattr(job, "asset_layer", None)
    if layer is None:
        return set()
    keys = getattr(layer, "selected_asset_keys", None) or getattr(layer, "executable_asset_keys", None) or getattr(layer, "asset_keys", None)
    if keys:
        return {k.to_user_string() for k in keys}
    return set()


def _compras_frames(store: LandingStore, compras: dict):
    keys = store.year_partition_keys("compras_gov")
    if not keys and compras.get("key"):
        keys = [str(compras["key"])]
    return [store.read_parquet(key) for key in keys]


def _basicos_from_ref(store: LandingStore, compras: dict) -> set[str]:
    basicos: set[str] = set()
    for df in _compras_frames(store, compras):
        basicos |= cnpj_basicos_from_frame(df)
    return basicos


def _compras_ids(store: LandingStore, compras: dict) -> set[str]:
    ids: set[str] = set()
    for df in _compras_frames(store, compras):
        col = "numerocontrolepncp" if "numerocontrolepncp" in df.columns else None
        if not col:
            continue
        ids |= {str(v) for v in df[col].to_list() if v}
    return ids
