from __future__ import annotations

import calendar
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

import httpx
import polars as pl

from compras_ingest.cpf import assert_no_raw_cpf, mask_frame
from compras_ingest.ids import record_hash
from compras_ingest.landing import LandingRef, LandingStore, partition_date_of
from compras_ingest.pncp_ids import (
    complete_compra_keys,
    fixture_ibge_targets,
    is_complete_compra,
    live_ibge_targets,
)
from compras_ingest.official import (
    PNCP_API_BASE,
    PNCP_COMPRA_PATH,
    PNCP_CONSULTA_BASE,
    PNCP_HOSTS,
    PNCP_ITEM_RESULTADOS_PATH,
    PNCP_ITENS_PATH,
    PNCP_PUBLICACAO_PATH,
    PncpOfficial,
    assert_official_host,
    fixture_pncp_official,
    http_client,
    resolve_pncp_consulta,
)
from compras_ingest.settings import Settings
from compras_normalize.text import parse_datetime

SOURCE = "pncp_consulta"
CURSOR_KEY = "pncp_consulta/_cursor.json"
GAPS_CURSOR_KEY = "pncp_consulta/_gaps_cursor.json"
ROWS_KEY = "pncp_consulta/_rows.json"
PAGE_SIZE = 50
MIN_INTERVAL_S = 1.0
Clock = Callable[[], float]
Sleeper = Callable[[float], None]


@dataclass
class FetchResult:
    url: str
    status_code: int
    payload: object | None


class Transport:
    def get(self, url: str, params: dict | None = None) -> FetchResult:
        raise NotImplementedError


class RateLimiter:
    def __init__(
        self,
        min_interval: float = MIN_INTERVAL_S,
        sleeper: Sleeper | None = None,
        clock: Clock | None = None,
    ):
        if min_interval < MIN_INTERVAL_S:
            raise ValueError("PNCP consulta spacing must be >= 1s")
        import time

        self.min_interval = min_interval
        self._sleeper = sleeper or time.sleep
        self._clock = clock or time.monotonic
        self._last: float | None = None

    def wait(self) -> None:
        if self._last is not None:
            self._sleeper(self.min_interval)
        self._last = self._clock()


class LiveTransport(Transport):
    def __init__(self, client: httpx.Client, sleeper: Sleeper | None = None):
        import time

        self._client = client
        self._sleeper = sleeper or time.sleep

    def get(self, url: str, params: dict | None = None) -> FetchResult:
        assert_official_host(url, PNCP_HOSTS)
        delay = 1.0
        last_exc: Exception | None = None
        for _ in range(6):
            resp = self._client.get(url, params=params)
            assert_official_host(str(resp.url), PNCP_HOSTS)
            if resp.status_code in {429, 500, 502, 503, 504}:
                last_exc = RuntimeError(f"{url} returned {resp.status_code}")
                self._sleeper(delay)
                delay = min(delay * 2, 32)
                continue
            if resp.status_code == 204:
                return FetchResult(str(resp.url), 204, None)
            resp.raise_for_status()
            if not resp.content:
                return FetchResult(str(resp.url), resp.status_code, None)
            return FetchResult(str(resp.url), resp.status_code, resp.json())
        raise RuntimeError(f"PNCP request failed after retries: {last_exc}")


class FixtureTransport(Transport):
    def __init__(self, root: Path):
        self.root = root
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, params: dict | None = None) -> FetchResult:
        assert_official_host(url, PNCP_HOSTS)
        query = {k: _one(v) for k, v in (params or {}).items()}
        parsed = urlparse(url)
        if parsed.query:
            query.update({k: _one(v[0]) if v else "" for k, v in parse_qs(parsed.query).items()})
        self.calls.append((url, query))
        path = _fixture_file(self.root, parsed.path, query)
        if path is None or not path.exists():
            return FetchResult(url, 204, None)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return FetchResult(url, 200, payload)


class InterruptTransport(Transport):
    def __init__(self, inner: FixtureTransport, fail_on_publicacao_page: int):
        self.inner = inner
        self.fail_on_publicacao_page = fail_on_publicacao_page
        self.calls = inner.calls

    def get(self, url: str, params: dict | None = None) -> FetchResult:
        query = {k: _one(v) for k, v in (params or {}).items()}
        if PNCP_PUBLICACAO_PATH in urlparse(url).path and int(query.get("pagina") or 0) == self.fail_on_publicacao_page:
            self.inner.calls.append((url, query))
            raise RuntimeError("injected interrupt")
        return self.inner.get(url, params)


@dataclass
class PncpConsultaClient:
    transport: Transport
    limiter: RateLimiter
    official: PncpOfficial
    calls: list[str] = field(default_factory=list)

    def get(self, url: str, params: dict | None = None) -> FetchResult:
        assert_official_host(url, PNCP_HOSTS)
        self.limiter.wait()
        result = self.transport.get(url, params)
        assert_official_host(result.url, PNCP_HOSTS)
        self.calls.append(result.url)
        return result

    def publicacao(
        self,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        page: int,
        ibge: str,
        uf: str,
    ) -> dict | None:
        url = f"{self.official.consulta_base}{PNCP_PUBLICACAO_PATH}"
        result = self.get(
            url,
            {
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "codigoModalidadeContratacao": modalidade,
                "pagina": page,
                "tamanhoPagina": PAGE_SIZE,
                "codigoMunicipioIbge": ibge,
                "uf": uf,
            },
        )
        if result.status_code == 204 or result.payload is None:
            return None
        if not isinstance(result.payload, dict):
            raise RuntimeError("publicacao payload is not an object")
        return result.payload

    def compra(self, cnpj: str, ano: int, sequencial: int) -> dict | None:
        path = PNCP_COMPRA_PATH.format(cnpj=cnpj, ano=ano, sequencial=sequencial)
        result = self.get(f"{self.official.consulta_base}{path}")
        if result.status_code == 204 or result.payload is None:
            return None
        if not isinstance(result.payload, dict):
            raise RuntimeError("compra payload is not an object")
        return result.payload

    def itens(self, cnpj: str, ano: int, sequencial: int) -> list[dict]:
        path = PNCP_ITENS_PATH.format(cnpj=cnpj, ano=ano, sequencial=sequencial)
        result = self.get(f"{self.official.api_base}{path}")
        return _as_rows(result.payload)

    def resultados(self, cnpj: str, ano: int, sequencial: int, numero_item: int) -> tuple[int, list[dict]]:
        path = PNCP_ITEM_RESULTADOS_PATH.format(
            cnpj=cnpj, ano=ano, sequencial=sequencial, numeroItem=numero_item
        )
        result = self.get(f"{self.official.api_base}{path}")
        return result.status_code, _as_rows(result.payload)


def land_pncp_consulta(
    settings: Settings,
    store: LandingStore | None = None,
    official: PncpOfficial | None = None,
    transport: Transport | None = None,
    sleeper: Sleeper | None = None,
    clock: Clock | None = None,
    client_holder: httpx.Client | None = None,
    window: tuple[date, date] | None = None,
    gaps_only: bool = False,
    covered: set[tuple[str, int, int]] | None = None,
) -> tuple[LandingRef, pl.DataFrame, dict]:
    store = store or LandingStore(settings)
    if official is None:
        if settings.pncp_consulta_fetch:
            official = resolve_pncp_consulta()
        else:
            official = fixture_pncp_official()
    if official.consulta_base != PNCP_CONSULTA_BASE:
        raise RuntimeError(f"consulta base is not official: {official.consulta_base}")
    if httpx.URL(official.consulta_base).host not in PNCP_HOSTS:
        raise RuntimeError(f"consulta host is not official: {official.consulta_base}")
    limiter = RateLimiter(MIN_INTERVAL_S, sleeper=sleeper, clock=clock)
    owned_client = None
    if transport is None:
        if settings.pncp_consulta_fetch:
            owned_client = client_holder or http_client(timeout=90.0)
            transport = LiveTransport(owned_client, sleeper=sleeper)
        else:
            root = settings.pncp_consulta_dir
            if root is None:
                raise FileNotFoundError("PNCP_CONSULTA_DIR missing and PNCP_CONSULTA_FETCH is off")
            transport = FixtureTransport(root)
    client = PncpConsultaClient(transport, limiter, official)
    try:
        rows, report = _ingest(
            settings,
            store,
            client,
            official,
            window=window,
            gaps_only=gaps_only,
            covered=covered,
        )
    finally:
        if owned_client is not None and client_holder is None:
            owned_client.close()
    df = _frame(rows)
    df = mask_frame(df)
    _assert_no_raw_cpf_frame(df)
    if df.is_empty() and not report.get("resumed_empty") and not report.get("gaps_empty"):
        raise RuntimeError("pncp_consulta produced no rows")
    dates = [parse_datetime(v) for v in df["data_publicacao_pncp"].to_list()] if "data_publicacao_pncp" in df.columns else []
    part = partition_date_of(dates) if dates else datetime.now(timezone.utc).date().isoformat()
    ref = store.write_parquet(SOURCE, part, df)
    report.update(
        {
            "consulta_base": official.consulta_base,
            "api_base": official.api_base,
            "publicacao_url": f"{official.consulta_base}{PNCP_PUBLICACAO_PATH}",
            "mode": "fetch" if settings.pncp_consulta_fetch else "fixture",
            "gaps_only": gaps_only,
            "http_calls": len(client.calls),
            "trailing_window_days": settings.trailing_window_days,
        }
    )
    if window:
        report["window_start"] = window[0].isoformat()
        report["window_end"] = window[1].isoformat()
    store.put(
        f"{SOURCE}/date={ref.partition_date}/{ref.sha256}.source.json",
        json.dumps(report, indent=2).encode(),
    )
    return ref, df, report


def land_pncp_consulta_gaps(
    settings: Settings,
    store: LandingStore | None = None,
    official: PncpOfficial | None = None,
    transport: Transport | None = None,
    sleeper: Sleeper | None = None,
    clock: Clock | None = None,
    covered: set[tuple[str, int, int]] | None = None,
) -> tuple[LandingRef, pl.DataFrame, dict]:
    store = store or LandingStore(settings)
    covered = covered if covered is not None else complete_compra_keys(store)
    return land_pncp_consulta(
        settings,
        store,
        official=official,
        transport=transport,
        sleeper=sleeper,
        clock=clock,
        gaps_only=True,
        covered=covered,
    )


def _ingest(
    settings: Settings,
    store: LandingStore,
    client: PncpConsultaClient,
    official: PncpOfficial,
    window: tuple[date, date] | None = None,
    gaps_only: bool = False,
    covered: set[tuple[str, int, int]] | None = None,
) -> tuple[list[dict], dict]:
    year = settings.pncp_consulta_year
    targets = _targets(settings, official)
    windows, modalidades = _plan(settings, official, window=window)
    cursor_key = GAPS_CURSOR_KEY if gaps_only else CURSOR_KEY
    if gaps_only and covered is None:
        covered = complete_compra_keys(store)
    covered = covered or set()
    if gaps_only and not covered and not store.list_parquet("compras_gov"):
        raise RuntimeError("PNCP gaps need compras.gov landing for the covered slice")
    cursor = _read_cursor(store, cursor_key)
    target_ibges = {ibge for ibge, _ in targets}
    if _cursor_done(cursor, year, target_ibges):
        existing = _read_rows(store) or _rows_from_landing(store)
        return existing, {
            "resumed_empty": False,
            "done": True,
            "skipped_http": True,
            "gaps_only": gaps_only,
            "rows": len(existing),
        }
    start = _resume_point(cursor, targets, year, windows, modalidades)
    rows = _read_rows(store)
    if not rows:
        rows = _rows_from_landing(store)
    seen = {str(r.get("numero_controle_pncp") or "") for r in rows if r.get("numero_controle_pncp")}
    if cursor:
        seen.update(str(x) for x in (cursor.get("completed_ids") or []) if x)
    skipped = 0
    skipped_complete = 0
    fetched = 0
    started = False
    completed_ibges = set(str(x) for x in (cursor or {}).get("completed_ibges") or [])
    last_ibge = ""
    last_uf = ""
    for ibge, uf in targets:
        last_ibge, last_uf = ibge, uf
        if ibge in completed_ibges:
            continue
        for data_inicial, data_final in windows:
            for modalidade in modalidades:
                if not started:
                    if (ibge, data_inicial, data_final, modalidade) != start["window"]:
                        continue
                    started = True
                    page = int(start["page"])
                else:
                    page = 1
                same_window = (ibge, data_inicial, data_final, modalidade) == start["window"]
                last_id = start["last_id"] if same_window else ""
                while True:
                    payload = client.publicacao(data_inicial, data_final, modalidade, page, ibge, uf)
                    compras = _page_data(payload)
                    if not compras:
                        break
                    for compra in compras:
                        pncp_id = str(compra.get("numeroControlePNCP") or "")
                        if last_id and pncp_id == last_id:
                            last_id = ""
                            continue
                        if last_id:
                            continue
                        if pncp_id and pncp_id in seen:
                            skipped += 1
                            continue
                        if gaps_only and is_complete_compra(pncp_id, covered):
                            if pncp_id:
                                seen.add(pncp_id)
                            skipped_complete += 1
                            skipped += 1
                            _write_cursor(
                                store,
                                _cursor_payload(
                                    ibge,
                                    year,
                                    data_inicial,
                                    data_final,
                                    modalidade,
                                    page,
                                    pncp_id,
                                    seen,
                                    completed_ibges,
                                    False,
                                    gaps_only,
                                ),
                                cursor_key,
                            )
                            continue
                        cnpj, ano, sequencial = _compra_key(compra)
                        detail = client.compra(cnpj, ano, sequencial) or compra
                        items = client.itens(cnpj, ano, sequencial)
                        item_rows = items or [{}]
                        for item in item_rows:
                            resultados: list[dict] = []
                            resultado_http = None
                            numero = item.get("numeroItem")
                            if item.get("temResultado") and numero is not None:
                                resultado_http, resultados = client.resultados(
                                    cnpj, ano, sequencial, int(numero)
                                )
                            if not resultados:
                                resultados = [{}]
                            for resultado in resultados:
                                rows.append(_row(detail, item, resultado, resultado_http))
                        if pncp_id:
                            seen.add(pncp_id)
                        fetched += 1
                        _write_rows(store, rows)
                        _write_cursor(
                            store,
                            _cursor_payload(
                                ibge,
                                year,
                                data_inicial,
                                data_final,
                                modalidade,
                                page,
                                pncp_id,
                                seen,
                                completed_ibges,
                                False,
                                gaps_only,
                            ),
                            cursor_key,
                        )
                    total_pages = (payload or {}).get("totalPaginas")
                    if total_pages is not None:
                        if page >= int(total_pages):
                            break
                    elif len(compras) < PAGE_SIZE:
                        break
                    page += 1
                    _write_cursor(
                        store,
                        _cursor_payload(
                            ibge,
                            year,
                            data_inicial,
                            data_final,
                            modalidade,
                            page,
                            "",
                            seen,
                            completed_ibges,
                            False,
                            gaps_only,
                        ),
                        cursor_key,
                    )
        completed_ibges.add(ibge)
    _write_cursor(
        store,
        _cursor_payload(
            last_ibge,
            year,
            windows[-1][0] if windows else "",
            windows[-1][1] if windows else "",
            modalidades[-1] if modalidades else 0,
            1,
            "",
            seen,
            completed_ibges,
            True,
            gaps_only,
        ),
        cursor_key,
    )
    return rows, {
        "done": True,
        "skipped_http": False,
        "gaps_only": gaps_only,
        "gaps_empty": gaps_only and fetched == 0,
        "rows": len(rows),
        "fetched_compras": fetched,
        "skipped_compras": skipped,
        "skipped_complete": skipped_complete,
        "ibge": last_ibge,
        "ibges": [ibge for ibge, _ in targets],
        "year": year,
        "covered_n": len(covered),
    }


def _targets(settings: Settings, official: PncpOfficial) -> list[tuple[str, str]]:
    _ = official
    if settings.pncp_consulta_fetch:
        return live_ibge_targets()
    if settings.pncp_consulta_dir is None:
        raise FileNotFoundError("PNCP_CONSULTA_DIR missing")
    manifest_path = settings.pncp_consulta_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ibge = str(manifest.get("ibge") or settings.pncp_consulta_ibge)
        uf = str(manifest.get("uf") or settings.pncp_consulta_uf)
        return fixture_ibge_targets(ibge, uf)
    return fixture_ibge_targets(settings.pncp_consulta_ibge, settings.pncp_consulta_uf)


def _plan(
    settings: Settings,
    official: PncpOfficial,
    window: tuple[date, date] | None = None,
) -> tuple[list[tuple[str, str]], list[int]]:
    if settings.pncp_consulta_fetch:
        if window:
            return _windows_for_range(window[0], window[1]), list(official.modalidades)
        return _month_windows(settings.pncp_consulta_year), list(official.modalidades)
    root = settings.pncp_consulta_dir
    if root is None:
        raise FileNotFoundError("PNCP_CONSULTA_DIR missing")
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    windows = [(str(a), str(b)) for a, b in manifest.get("windows") or []]
    modalidades = [int(x) for x in manifest.get("modalidades") or []]
    if not windows or not modalidades:
        raise RuntimeError("pncp_consulta manifest needs windows and modalidades")
    return windows, modalidades


def _month_windows(year: int) -> list[tuple[str, str]]:
    out = []
    for month in range(1, 13):
        last = calendar.monthrange(year, month)[1]
        out.append((f"{year}{month:02d}01", f"{year}{month:02d}{last:02d}"))
    return out


def _windows_for_range(start: date, end: date) -> list[tuple[str, str]]:
    if end < start:
        raise ValueError("trailing window end is before start")
    out: list[tuple[str, str]] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        last = calendar.monthrange(year, month)[1]
        lo = max(date(year, month, 1), start)
        hi = min(date(year, month, last), end)
        out.append((lo.strftime("%Y%m%d"), hi.strftime("%Y%m%d")))
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return out


def _resume_point(
    cursor: dict | None,
    targets: list[tuple[str, str]],
    year: int,
    windows: list[tuple[str, str]],
    modalidades: list[int],
) -> dict:
    first_ibge = targets[0][0]
    first = {"window": (first_ibge, windows[0][0], windows[0][1], modalidades[0]), "page": 1, "last_id": ""}
    if not cursor or int(cursor.get("year") or 0) != year:
        return first
    ibge = str(cursor.get("ibge") or "")
    if ibge not in {code for code, _ in targets}:
        return first
    data_inicial = str(cursor.get("data_inicial") or "")
    data_final = str(cursor.get("data_final") or "")
    modalidade = int(cursor.get("modalidade") or 0)
    if (data_inicial, data_final) not in windows or modalidade not in modalidades:
        return first
    return {
        "window": (ibge, data_inicial, data_final, modalidade),
        "page": int(cursor.get("page") or 1),
        "last_id": str(cursor.get("last_id") or ""),
    }


def _cursor_done(cursor: dict | None, year: int, target_ibges: set[str]) -> bool:
    if not cursor or not cursor.get("done") or int(cursor.get("year") or 0) != year:
        return False
    done = {str(x) for x in (cursor.get("completed_ibges") or []) if x}
    if cursor.get("ibge"):
        done.add(str(cursor["ibge"]))
    return target_ibges <= done


def _cursor_payload(
    ibge: str,
    year: int,
    data_inicial: str,
    data_final: str,
    modalidade: int,
    page: int,
    last_id: str,
    seen: set[str],
    completed_ibges: set[str],
    done: bool,
    gaps_only: bool,
) -> dict:
    return {
        "ibge": ibge,
        "year": year,
        "data_inicial": data_inicial,
        "data_final": data_final,
        "modalidade": modalidade,
        "page": page,
        "last_id": last_id,
        "completed_ids": sorted(seen),
        "completed_ibges": sorted(completed_ibges),
        "done": done,
        "gaps_only": gaps_only,
    }


def _read_cursor(store: LandingStore, key: str = CURSOR_KEY) -> dict | None:
    if not store.exists(key):
        return None
    return json.loads(store.get(key).decode())


def _write_cursor(store: LandingStore, cursor: dict, key: str = CURSOR_KEY) -> None:
    store.put_replace(key, json.dumps(cursor, indent=2).encode())


def _read_rows(store: LandingStore) -> list[dict]:
    if not store.exists(ROWS_KEY):
        return []
    payload = json.loads(store.get(ROWS_KEY).decode())
    if not isinstance(payload, list):
        raise RuntimeError("pncp_consulta staged rows are not a list")
    return [row for row in payload if isinstance(row, dict)]


def _write_rows(store: LandingStore, rows: list[dict]) -> None:
    store.put_replace(ROWS_KEY, json.dumps(rows, ensure_ascii=False).encode())


def _rows_from_landing(store: LandingStore) -> list[dict]:
    rows: list[dict] = []
    for key in store.list_parquet(SOURCE):
        df = store.read_parquet(key)
        if df.is_empty():
            continue
        rows.extend(df.to_dicts())
    return rows


def _page_data(payload: dict | None) -> list[dict]:
    if not payload:
        return []
    data = payload.get("data")
    if data is None:
        return []
    if not isinstance(data, list):
        raise RuntimeError("publicacao data is not a list")
    return [row for row in data if isinstance(row, dict)]


def _compra_key(compra: dict) -> tuple[str, int, int]:
    org = compra.get("orgaoEntidade") or {}
    cnpj = "".join(c for c in str(org.get("cnpj") or "") if c.isdigit())
    ano = int(compra.get("anoCompra") or 0)
    sequencial = int(compra.get("sequencialCompra") or 0)
    if not cnpj or ano < 1 or sequencial < 1:
        raise RuntimeError(f"compra missing identity: {compra.get('numeroControlePNCP')}")
    return cnpj, ano, sequencial


def _row(compra: dict, item: dict, resultado: dict, resultado_http: int | None = None) -> dict:
    org = compra.get("orgaoEntidade") or {}
    unid = compra.get("unidadeOrgao") or {}
    pncp_id = str(compra.get("numeroControlePNCP") or "")
    numero_item = item.get("numeroItem")
    seq_res = resultado.get("sequencialResultado")
    record_id = f"{pncp_id}:{numero_item or 0}:{seq_res or 0}"
    payload = {
        "numero_controle_pncp": pncp_id,
        "orgao_cnpj": str(org.get("cnpj") or ""),
        "orgao_razao": str(org.get("razaoSocial") or ""),
        "esfera": str(org.get("esferaId") or ""),
        "poder": str(org.get("poderId") or ""),
        "uf": str(unid.get("ufSigla") or ""),
        "municipio_nome": str(unid.get("municipioNome") or ""),
        "municipio_ibge": str(unid.get("codigoIbge") or ""),
        "modalidade_id": compra.get("modalidadeId"),
        "modalidade_nome": str(compra.get("modalidadeNome") or ""),
        "objeto": str(compra.get("objetoCompra") or ""),
        "valor_total_homologado": compra.get("valorTotalHomologado"),
        "data_publicacao_pncp": str(compra.get("dataPublicacaoPncp") or ""),
        "ano": compra.get("anoCompra"),
        "sequencial": compra.get("sequencialCompra"),
        "numero_item": numero_item,
        "descricao": str(item.get("descricao") or ""),
        "material_ou_servico": str(item.get("materialOuServico") or ""),
        "quantidade": item.get("quantidade"),
        "unidade_medida": str(item.get("unidadeMedida") or ""),
        "valor_unitario_estimado": item.get("valorUnitarioEstimado"),
        "valor_total": item.get("valorTotal"),
        "catalogo_codigo_item": str(item.get("catalogoCodigoItem") or ""),
        "ni_fornecedor": str(resultado.get("niFornecedor") or ""),
        "nome_fornecedor": str(resultado.get("nomeRazaoSocialFornecedor") or ""),
        "tipo_pessoa": str(resultado.get("tipoPessoa") or ""),
        "valor_unitario_homologado": resultado.get("valorUnitarioHomologado"),
        "valor_unitario_resultado": resultado.get("valorUnitarioHomologado"),
        "quantidade_homologada": resultado.get("quantidadeHomologada"),
        "situacao": str(
            item.get("situacaoCompraItemNome") or compra.get("situacaoCompraNome") or ""
        ),
        "resultado_http": resultado_http,
        "source": SOURCE,
        "record_id": record_id,
    }
    payload["record_hash"] = record_hash({k: v for k, v in payload.items() if k not in {"record_hash"}})
    return payload


def _frame(rows: list[dict]) -> pl.DataFrame:
    if not rows:
        return pl.DataFrame(schema={c: pl.String for c in _empty_cols()})
    hashed = []
    for row in rows:
        if "record_hash" not in row:
            row = dict(row)
            row["record_hash"] = record_hash({k: v for k, v in row.items() if k not in {"record_hash"}})
        hashed.append(row)
    return pl.DataFrame(hashed)


def _empty_cols() -> list[str]:
    return [
        "numero_controle_pncp",
        "orgao_cnpj",
        "orgao_razao",
        "esfera",
        "poder",
        "uf",
        "municipio_nome",
        "municipio_ibge",
        "modalidade_id",
        "modalidade_nome",
        "objeto",
        "valor_total_homologado",
        "data_publicacao_pncp",
        "ano",
        "sequencial",
        "numero_item",
        "descricao",
        "material_ou_servico",
        "quantidade",
        "unidade_medida",
        "valor_unitario_estimado",
        "valor_total",
        "catalogo_codigo_item",
        "ni_fornecedor",
        "nome_fornecedor",
        "tipo_pessoa",
        "valor_unitario_homologado",
        "valor_unitario_resultado",
        "quantidade_homologada",
        "situacao",
        "resultado_http",
        "source",
        "record_id",
        "record_hash",
    ]


def _as_rows(payload: object | None) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
    raise RuntimeError("items payload is not a list")


def _fixture_file(root: Path, path: str, query: dict) -> Path | None:
    if path.endswith(PNCP_PUBLICACAO_PATH):
        key = f"{query.get('dataInicial')}_{query.get('dataFinal')}_{query.get('codigoModalidadeContratacao')}_p{query.get('pagina')}.json"
        return root / "publicacao" / key
    marker = "/v1/orgaos/"
    if marker not in path:
        return None
    tail = path.split(marker, 1)[1]
    parts = [p for p in tail.split("/") if p]
    if len(parts) < 4:
        return None
    cnpj, kind, ano, sequencial = parts[0], parts[1], parts[2], parts[3]
    if kind != "compras":
        return None
    rest = parts[4:]
    if rest == ["itens"]:
        return root / "itens" / f"{cnpj}_{ano}_{sequencial}.json"
    if len(rest) == 3 and rest[0] == "itens" and rest[2] == "resultados":
        return root / "resultados" / f"{cnpj}_{ano}_{sequencial}_{rest[1]}.json"
    if not rest:
        return root / "compras" / f"{cnpj}_{ano}_{sequencial}.json"
    return None


def _one(value: object) -> str:
    return str(value)


def _assert_no_raw_cpf_frame(df: pl.DataFrame) -> None:
    if df.is_empty():
        return
    blobs = [str(v) for col in df.columns for v in df[col].to_list() if v is not None]
    assert_no_raw_cpf(blobs)
