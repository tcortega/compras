from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

import clickhouse_connect
import polars as pl
import psycopg
from psycopg.rows import dict_row

from compras_ingest.ids import contratacao_id, flag_id, fornecedor_id, item_id, orgao_id
from compras_ingest.landing import LandingStore
from compras_ingest.settings import Settings
from compras_normalize.text import parse_date, parse_datetime, parse_decimal

PUBLIC_LANDING_SOURCES = (
    ("compras_gov", "compras_gov"),
    ("receita_cnpj", "receita_cnpj"),
    ("ocds", "ocds"),
    ("pncp_consulta", "pncp_consulta"),
    ("tce_sp_licitacao", "tce_sp"),
    ("tce_rs_licitacon", "tce_rs"),
    ("cgu_ceis_cnep", "cgu_ceis_cnep"),
)

_NOW = lambda: datetime.now(timezone.utc)


def apply_schema(settings: Settings) -> None:
    root = _repo_root()
    pg_sql = (root / "infra" / "postgres" / "01_compras.sql").read_text()
    with psycopg.connect(settings.postgres_dsn, autocommit=True) as conn:
        for stmt in _split_sql(pg_sql):
            conn.execute(stmt)
    parsed = urlparse(settings.clickhouse_url)
    ch = clickhouse_connect.get_client(
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 8123,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
    )
    ch_sql = (root / "infra" / "clickhouse" / "01_item_fact.sql").read_text()
    for stmt in _split_sql(ch_sql):
        ch.command(stmt)


def write_entities(settings: Settings, items: pl.DataFrame) -> dict[str, int]:
    now = _NOW()
    orgaos: dict[str, dict] = {}
    fornecedores: dict[str, dict] = {}
    contratacoes: dict[str, dict] = {}
    item_rows: list[dict] = []
    for row in items.iter_rows(named=True):
        ocnpj = str(row.get("orgao_cnpj") or "")
        if ocnpj:
            orgaos[ocnpj] = {
                "id": orgao_id(ocnpj),
                "cnpj": ocnpj,
                "razaoSocial": row.get("orgao_razao") or "",
                "esfera": row.get("esfera") or "municipal",
                "poder": row.get("poder") or "executivo",
                "uf": row.get("uf") or "",
                "municipioIbge": row.get("municipio_ibge") or "",
                "municipioNome": row.get("municipio_nome") or "",
            }
        fcnpj = str(row.get("fornecedor_cnpj") or "")
        fid = None
        if len(fcnpj) == 14:
            fid = fornecedor_id(fcnpj)
            fornecedores[fcnpj] = {
                "id": fid,
                "cnpj": fcnpj,
                "razaoSocial": row.get("fornecedor_razao") or "",
                "openedOn": parse_date(row.get("opened_on")),
                "cnae": row.get("cnae") or None,
            }
        pncp = str(row.get("pncp_id") or "")
        cid = contratacao_id(pncp)
        contratacoes[pncp] = {
            "id": cid,
            "pncpId": pncp,
            "orgaoId": orgaos[ocnpj]["id"] if ocnpj else None,
            "modalidade": row.get("modalidade") or "",
            "objeto": row.get("objeto") or "",
            "ano": int(str(row.get("ano") or "0")[:4] or 0),
            "valorHomologado": parse_decimal(row.get("valor_homologado")),
            "publicadoEm": parse_datetime(row.get("publicado_em")),
            "source": row.get("source") or "compras_gov",
            "snapshotId": row.get("snapshot_id") or "",
            "methodologyVersion": row.get("methodology_version") or "",
        }
        rid = str(row.get("record_id") or "")
        item_rows.append(
            {
                "id": item_id(pncp, rid),
                "contratacaoId": cid,
                "fornecedorId": fid,
                "descricao": row.get("descricao") or "",
                "catmat": row.get("catmat") or None,
                "catser": row.get("catser") or None,
                "quantidade": parse_decimal(row.get("quantidade")) or Decimal("0"),
                "unidadeMedida": row.get("unidade_medida") or "",
                "unidadeCanonica": row.get("unidade_canonica") or None,
                "valorUnitario": parse_decimal(row.get("valor_unitario")),
                "valorTotal": parse_decimal(row.get("valor_total")),
                "valorPorUnidadeCanonica": parse_decimal(
                    row.get("valor_por_unidade_canonica") or row.get("valor_unitario_base")
                ),
                "specConcentracao": row.get("spec_concentracao") or None,
                "specDosagem": row.get("spec_dosagem") or None,
                "specTamanho": row.get("spec_tamanho") or None,
                "uf": row.get("uf_item") or row.get("uf") or "",
                "quarter": row.get("quarter") or "",
                "snapshotId": row.get("snapshot_id") or "",
                "methodologyVersion": row.get("methodology_version") or "",
                "record_id": rid,
            }
        )
    with psycopg.connect(settings.postgres_dsn) as conn:
        _upsert_orgaos(conn, list(orgaos.values()), now)
        _upsert_fornecedores(conn, list(fornecedores.values()), now)
        _upsert_contratacoes(conn, list(contratacoes.values()), now)
        _upsert_items(conn, item_rows, now)
        conn.commit()
    return {
        "orgao": len(orgaos),
        "fornecedor": len(fornecedores),
        "contratacao": len(contratacoes),
        "item": len(item_rows),
    }


def write_facts(settings: Settings, items: pl.DataFrame) -> int:
    if items.is_empty():
        return 0
    ch = _ch(settings)
    cols = [
        "item_id",
        "contratacao_id",
        "fornecedor_id",
        "orgao_id",
        "pncp_id",
        "descricao",
        "catmat",
        "catser",
        "quantidade",
        "unidade_medida",
        "unidade_canonica",
        "valor_unitario",
        "valor_total",
        "valor_unitario_base",
        "valor_por_unidade_canonica",
        "spec_concentracao",
        "spec_dosagem",
        "spec_tamanho",
        "uf",
        "quarter",
        "snapshot_id",
        "methodology_version",
        "source",
        "record_hash",
        "publicado_em",
    ]
    data = []
    for row in items.iter_rows(named=True):
        ocnpj = str(row.get("orgao_cnpj") or "")
        fcnpj = str(row.get("fornecedor_cnpj") or "")
        pncp = str(row.get("pncp_id") or "")
        rid = str(row.get("record_id") or "")
        data.append(
            [
                item_id(pncp, rid),
                contratacao_id(pncp),
                fornecedor_id(fcnpj) if len(fcnpj) == 14 else None,
                orgao_id(ocnpj) if ocnpj else None,
                pncp,
                row.get("descricao") or "",
                row.get("catmat") or None,
                row.get("catser") or None,
                _f(parse_decimal(row.get("quantidade"))),
                row.get("unidade_medida") or "",
                row.get("unidade_canonica") or None,
                _f(parse_decimal(row.get("valor_unitario"))),
                _f(parse_decimal(row.get("valor_total"))),
                _f(parse_decimal(row.get("valor_por_unidade_canonica") or row.get("valor_unitario_base"))),
                _f(parse_decimal(row.get("valor_por_unidade_canonica") or row.get("valor_unitario_base"))),
                row.get("spec_concentracao") or None,
                row.get("spec_dosagem") or None,
                row.get("spec_tamanho") or None,
                row.get("uf_item") or row.get("uf") or "",
                row.get("quarter") or "",
                row.get("snapshot_id") or "",
                row.get("methodology_version") or "",
                row.get("source") or "compras_gov",
                row.get("record_hash") or "",
                parse_datetime(row.get("publicado_em")),
            ]
        )
    ch.insert(f"{settings.clickhouse_database}.item_fact", data, column_names=cols)
    return len(data)


def write_flags(settings: Settings, flags: pl.DataFrame, items: pl.DataFrame) -> int:
    if flags.is_empty():
        return 0
    item_by_record = {}
    for row in items.iter_rows(named=True):
        item_by_record[str(row.get("record_id") or "")] = (
            item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or "")),
            row.get("snapshot_id") or "",
            row.get("methodology_version") or "",
        )
    now = _NOW()
    rows = []
    for row in flags.iter_rows(named=True):
        rid = str(row.get("record_id") or "")
        mapped = item_by_record.get(rid)
        if not mapped:
            continue
        iid, snap, meth = mapped
        snap = str(row.get("snapshot_id") or snap)
        meth = str(row.get("methodology_version") or meth)
        rows.append(
            {
                "id": flag_id(iid, str(row["kind"]), snap),
                "itemId": iid,
                "kind": row["kind"],
                "delta": row["delta"],
                "sourceUrl": row.get("source_url") or "",
                "snapshotId": snap,
                "methodologyVersion": meth,
            }
        )
    if not rows:
        return 0
    sql = """
    INSERT INTO flag (
      id, "itemId", kind, state, "detectedAt", "notifiedAt", "publishAfter",
      "publishedAt", delta, "sourceUrl", "snapshotId", "methodologyVersion",
      "replyText", "repliedAt", suspended, "createdAt", "updatedAt"
    ) VALUES (
      %(id)s, %(itemId)s, %(kind)s, 'detected', %(now)s, NULL, NULL,
      NULL, %(delta)s, %(sourceUrl)s, %(snapshotId)s, %(methodologyVersion)s,
      NULL, NULL, false, %(now)s, %(now)s
    )
    ON CONFLICT (id) DO UPDATE SET
      delta = EXCLUDED.delta,
      "updatedAt" = EXCLUDED."updatedAt"
    """
    with psycopg.connect(settings.postgres_dsn) as conn:
        for row in rows:
            conn.execute(sql, {**row, "now": now})
        conn.commit()
    return len(rows)


def write_exclusions(settings: Settings, exclusions: pl.DataFrame, items: pl.DataFrame) -> int:
    if exclusions.is_empty():
        return 0
    item_by_record = {}
    for row in items.iter_rows(named=True):
        item_by_record[str(row.get("record_id") or "")] = (
            item_id(str(row.get("pncp_id") or ""), str(row.get("record_id") or "")),
            row.get("snapshot_id") or "",
            row.get("methodology_version") or "",
        )
    now = _NOW()
    rows = []
    for row in exclusions.iter_rows(named=True):
        rid = str(row.get("record_id") or "")
        mapped = item_by_record.get(rid)
        if not mapped:
            continue
        iid, snap, meth = mapped
        rows.append(
            {
                "itemId": iid,
                "reason": row["reason"],
                "detail": row.get("detail") or "",
                "snapshotId": str(row.get("snapshot_id") or snap),
                "methodologyVersion": str(row.get("methodology_version") or meth),
            }
        )
    if not rows:
        return 0
    sql = """
    INSERT INTO item_exclusion (
      "itemId", reason, detail, "snapshotId", "methodologyVersion", "createdAt"
    ) VALUES (
      %(itemId)s, %(reason)s, %(detail)s, %(snapshotId)s, %(methodologyVersion)s, %(now)s
    )
    ON CONFLICT ("itemId", reason) DO UPDATE SET
      detail = EXCLUDED.detail,
      "snapshotId" = EXCLUDED."snapshotId",
      "methodologyVersion" = EXCLUDED."methodologyVersion"
    """
    with psycopg.connect(settings.postgres_dsn) as conn:
        for row in rows:
            conn.execute(sql, {**row, "now": now})
        conn.commit()
    return len(rows)


def write_adjacencies(settings: Settings, edges: pl.DataFrame) -> int:
    if edges.is_empty():
        return 0
    now = _NOW()
    rows = []
    for row in edges.iter_rows(named=True):
        left = str(row.get("leftCnpj") or "")
        right = str(row.get("rightCnpj") or "")
        if not left or not right or left == right:
            continue
        if left > right:
            left, right = right, left
        rows.append(
            {
                "kind": str(row["kind"]),
                "leftCnpj": left,
                "rightCnpj": right,
                "evidence": str(row.get("evidence") or ""),
                "snapshotId": str(row.get("snapshot_id") or row.get("snapshotId") or ""),
                "methodologyVersion": str(
                    row.get("methodology_version") or row.get("methodologyVersion") or ""
                ),
            }
        )
    if not rows:
        return 0
    sql = """
    INSERT INTO fornecedor_adjacency (
      kind, "leftCnpj", "rightCnpj", evidence, "snapshotId", "methodologyVersion", "createdAt"
    ) VALUES (
      %(kind)s, %(leftCnpj)s, %(rightCnpj)s, %(evidence)s, %(snapshotId)s,
      %(methodologyVersion)s, %(now)s
    )
    ON CONFLICT (kind, "leftCnpj", "rightCnpj") DO UPDATE SET
      evidence = EXCLUDED.evidence,
      "snapshotId" = EXCLUDED."snapshotId",
      "methodologyVersion" = EXCLUDED."methodologyVersion"
    """
    with psycopg.connect(settings.postgres_dsn) as conn:
        for row in rows:
            conn.execute(sql, {**row, "now": now})
        conn.commit()
    return len(rows)


def fetch_adjacencies(
    settings: Settings,
    *,
    kind: str | None = None,
    cnpj: str | None = None,
) -> list[dict]:
    clauses: list[str] = []
    params: dict = {}
    if kind:
        clauses.append("kind = %(kind)s")
        params["kind"] = kind
    if cnpj:
        clauses.append('("leftCnpj" = %(cnpj)s OR "rightCnpj" = %(cnpj)s)')
        params["cnpj"] = cnpj
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f'SELECT * FROM fornecedor_adjacency {where} ORDER BY kind, "leftCnpj", "rightCnpj"'
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return list(conn.execute(sql, params).fetchall())


def fetch_counts(settings: Settings) -> dict[str, int]:
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        counts = {}
        for table in (
            "orgao",
            "fornecedor",
            "contratacao",
            "item",
            "flag",
            "item_exclusion",
            "catalog_code",
            "landing_source",
            "fornecedor_adjacency",
        ):
            counts[table] = conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
    return counts


def fetch_one_orgao(settings: Settings, cnpj: str) -> dict | None:
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return conn.execute('SELECT * FROM orgao WHERE cnpj = %s', (cnpj,)).fetchone()


def fetch_orgaos(settings: Settings) -> list[dict]:
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return list(conn.execute('SELECT * FROM orgao ORDER BY "municipioIbge", cnpj').fetchall())


def fetch_contratacao(settings: Settings, pncp_id: str) -> dict | None:
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return conn.execute('SELECT * FROM contratacao WHERE "pncpId" = %s', (pncp_id,)).fetchone()


def fetch_all_items(settings: Settings) -> list[dict]:
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return list(conn.execute("SELECT * FROM item ORDER BY descricao, id").fetchall())


def item_columns(settings: Settings) -> set[str]:
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        rows = conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'item'
            """
        ).fetchall()
    return {str(row["column_name"]) for row in rows}


def fetch_item_facts(settings: Settings) -> list[dict]:
    ch = _ch(settings)
    result = ch.query(
        f"""
        SELECT
          unidade_medida,
          unidade_canonica,
          valor_unitario,
          valor_unitario_base,
          valor_por_unidade_canonica,
          spec_concentracao,
          spec_dosagem,
          spec_tamanho
        FROM {settings.clickhouse_database}.item_fact
        FINAL
        """
    )
    return [dict(zip(result.column_names, row, strict=True)) for row in result.result_rows]


def fact_columns(settings: Settings) -> set[str]:
    ch = _ch(settings)
    result = ch.query(f"DESCRIBE TABLE {settings.clickhouse_database}.item_fact")
    names = result.column_names
    name_idx = names.index("name") if "name" in names else 0
    return {str(row[name_idx]) for row in result.result_rows}


def fetch_items_for(settings: Settings, contratacao_uuid: str) -> list[dict]:
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return list(
            conn.execute('SELECT * FROM item WHERE "contratacaoId" = %s', (contratacao_uuid,)).fetchall()
        )


def fetch_flags(
    settings: Settings,
    *,
    kind: str | None = None,
    state: str | None = None,
    item_id: str | None = None,
) -> list[dict]:
    clauses: list[str] = []
    params: dict = {}
    if kind:
        clauses.append("kind = %(kind)s")
        params["kind"] = kind
    if state:
        clauses.append("state = %(state)s")
        params["state"] = state
    if item_id:
        clauses.append('"itemId" = %(item_id)s')
        params["item_id"] = item_id
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f'SELECT * FROM flag {where} ORDER BY kind, "itemId", id'
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return list(conn.execute(sql, params).fetchall())


def fetch_exclusions(
    settings: Settings,
    *,
    reason: str | None = None,
    snapshot_id: str | None = None,
    item_id: str | None = None,
) -> list[dict]:
    clauses: list[str] = []
    params: dict = {}
    if reason:
        clauses.append("reason = %(reason)s")
        params["reason"] = reason
    if snapshot_id:
        clauses.append('"snapshotId" = %(snapshot_id)s')
        params["snapshot_id"] = snapshot_id
    if item_id:
        clauses.append('"itemId" = %(item_id)s')
        params["item_id"] = item_id
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f'SELECT * FROM item_exclusion {where} ORDER BY reason, "itemId"'
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return list(conn.execute(sql, params).fetchall())


def write_catalog(settings: Settings, catalog_df: pl.DataFrame) -> int:
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in catalog_df.iter_rows(named=True):
        code = _catalog_int(
            row.get("codigo") or row.get("codigoItem") or row.get("codigoitem") or row.get("codigoServico")
        )
        if not code:
            continue
        tipo = str(row.get("tipo") or "M").strip().upper()[:1]
        kind = "catser" if tipo == "S" else "catmat"
        key = (code, kind)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"codigo": code, "kind": kind})
    if not rows:
        return 0
    sql = """
    INSERT INTO catalog_code (codigo, kind)
    VALUES (%(codigo)s, %(kind)s)
    ON CONFLICT (codigo, kind) DO NOTHING
    """
    with psycopg.connect(settings.postgres_dsn) as conn:
        for row in rows:
            conn.execute(sql, row)
        conn.commit()
    return len(rows)


def write_landing_sources(settings: Settings, store: LandingStore) -> dict[str, dict]:
    written: dict[str, dict] = {}
    sql = """
    INSERT INTO landing_source (name, "lastUpdate", n, "snapshotId")
    VALUES (%(name)s, %(lastUpdate)s, %(n)s, %(snapshotId)s)
    ON CONFLICT (name) DO UPDATE SET
      "lastUpdate" = EXCLUDED."lastUpdate",
      n = EXCLUDED.n,
      "snapshotId" = EXCLUDED."snapshotId"
    """
    with psycopg.connect(settings.postgres_dsn) as conn:
        for landing_name, public_name in PUBLIC_LANDING_SOURCES:
            n, last_update, snap = _landing_freshness(store, landing_name)
            row = {"name": public_name, "lastUpdate": last_update, "n": n, "snapshotId": snap}
            if n == 0 and last_update is None:
                continue
            conn.execute(sql, row)
            written[public_name] = row
        conn.commit()
    return written


def fetch_catalog_codes(settings: Settings) -> list[dict]:
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return list(conn.execute("SELECT codigo, kind FROM catalog_code ORDER BY kind, codigo").fetchall())


def fetch_landing_sources(settings: Settings) -> list[dict]:
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        return list(conn.execute('SELECT name, "lastUpdate", n, "snapshotId" FROM landing_source ORDER BY name').fetchall())


def fetch_raw_text_blobs(settings: Settings) -> list[str]:
    blobs: list[str] = []
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as conn:
        for table in (
            "orgao",
            "fornecedor",
            "contratacao",
            "item",
            "flag",
            "item_exclusion",
            "catalog_code",
            "landing_source",
            "fornecedor_adjacency",
        ):
            for row in conn.execute(f"SELECT * FROM {table}").fetchall():
                blobs.extend(str(v) for v in row.values() if v is not None)
    return blobs


def _upsert_orgaos(conn, rows: list[dict], now) -> None:
    sql = """
    INSERT INTO orgao (
      id, cnpj, "razaoSocial", esfera, poder, uf, "municipioIbge", "municipioNome",
      suspended, "createdAt", "updatedAt"
    ) VALUES (
      %(id)s, %(cnpj)s, %(razaoSocial)s, %(esfera)s, %(poder)s, %(uf)s,
      %(municipioIbge)s, %(municipioNome)s, false, %(now)s, %(now)s
    )
    ON CONFLICT (cnpj) DO UPDATE SET
      "razaoSocial" = EXCLUDED."razaoSocial",
      esfera = EXCLUDED.esfera,
      poder = EXCLUDED.poder,
      uf = EXCLUDED.uf,
      "municipioIbge" = EXCLUDED."municipioIbge",
      "municipioNome" = EXCLUDED."municipioNome",
      "updatedAt" = EXCLUDED."updatedAt"
    """
    for row in rows:
        conn.execute(sql, {**row, "now": now})


def _upsert_fornecedores(conn, rows: list[dict], now) -> None:
    sql = """
    INSERT INTO fornecedor (
      id, cnpj, "razaoSocial", "openedOn", cnae, suspended, "createdAt", "updatedAt"
    ) VALUES (
      %(id)s, %(cnpj)s, %(razaoSocial)s, %(openedOn)s, %(cnae)s, false, %(now)s, %(now)s
    )
    ON CONFLICT (cnpj) DO UPDATE SET
      "razaoSocial" = EXCLUDED."razaoSocial",
      "openedOn" = COALESCE(EXCLUDED."openedOn", fornecedor."openedOn"),
      cnae = COALESCE(EXCLUDED.cnae, fornecedor.cnae),
      "updatedAt" = EXCLUDED."updatedAt"
    """
    for row in rows:
        conn.execute(sql, {**row, "now": now})


def _upsert_contratacoes(conn, rows: list[dict], now) -> None:
    sql = """
    INSERT INTO contratacao (
      id, "pncpId", "orgaoId", modalidade, objeto, ano, "valorHomologado",
      "publicadoEm", source, "snapshotId", "methodologyVersion",
      suspended, "createdAt", "updatedAt"
    ) VALUES (
      %(id)s, %(pncpId)s, %(orgaoId)s, %(modalidade)s, %(objeto)s, %(ano)s,
      %(valorHomologado)s, %(publicadoEm)s, %(source)s, %(snapshotId)s,
      %(methodologyVersion)s, false, %(now)s, %(now)s
    )
    ON CONFLICT ("pncpId") DO UPDATE SET
      "orgaoId" = EXCLUDED."orgaoId",
      modalidade = EXCLUDED.modalidade,
      objeto = EXCLUDED.objeto,
      ano = EXCLUDED.ano,
      "valorHomologado" = EXCLUDED."valorHomologado",
      "publicadoEm" = EXCLUDED."publicadoEm",
      source = EXCLUDED.source,
      "snapshotId" = EXCLUDED."snapshotId",
      "methodologyVersion" = EXCLUDED."methodologyVersion",
      "updatedAt" = EXCLUDED."updatedAt"
    """
    for row in rows:
        conn.execute(sql, {**row, "now": now})


def _upsert_items(conn, rows: list[dict], now) -> None:
    sql = """
    INSERT INTO item (
      id, "contratacaoId", "fornecedorId", descricao, catmat, catser,
      quantidade, "unidadeMedida", "unidadeCanonica", "valorUnitario", "valorTotal",
      "valorPorUnidadeCanonica",
      "specConcentracao", "specDosagem", "specTamanho",
      uf, quarter, "snapshotId", "methodologyVersion",
      suspended, "createdAt", "updatedAt"
    ) VALUES (
      %(id)s, %(contratacaoId)s, %(fornecedorId)s, %(descricao)s, %(catmat)s, %(catser)s,
      %(quantidade)s, %(unidadeMedida)s, %(unidadeCanonica)s, %(valorUnitario)s, %(valorTotal)s,
      %(valorPorUnidadeCanonica)s,
      %(specConcentracao)s, %(specDosagem)s, %(specTamanho)s,
      %(uf)s, %(quarter)s, %(snapshotId)s, %(methodologyVersion)s,
      false, %(now)s, %(now)s
    )
    ON CONFLICT (id) DO UPDATE SET
      "fornecedorId" = EXCLUDED."fornecedorId",
      descricao = EXCLUDED.descricao,
      catmat = EXCLUDED.catmat,
      catser = EXCLUDED.catser,
      quantidade = EXCLUDED.quantidade,
      "unidadeMedida" = EXCLUDED."unidadeMedida",
      "unidadeCanonica" = EXCLUDED."unidadeCanonica",
      "valorUnitario" = EXCLUDED."valorUnitario",
      "valorTotal" = EXCLUDED."valorTotal",
      "valorPorUnidadeCanonica" = EXCLUDED."valorPorUnidadeCanonica",
      "specConcentracao" = EXCLUDED."specConcentracao",
      "specDosagem" = EXCLUDED."specDosagem",
      "specTamanho" = EXCLUDED."specTamanho",
      uf = EXCLUDED.uf,
      quarter = EXCLUDED.quarter,
      "snapshotId" = EXCLUDED."snapshotId",
      "methodologyVersion" = EXCLUDED."methodologyVersion",
      "updatedAt" = EXCLUDED."updatedAt"
    """
    for row in rows:
        payload = {k: v for k, v in row.items() if k != "record_id"}
        conn.execute(sql, {**payload, "now": now})


def _catalog_int(value) -> str:
    raw = str(value or "").strip()
    if raw == "" or raw.lower() in {"nan", "none", "null", "-"}:
        return ""
    parsed = parse_decimal(raw)
    if parsed is None or parsed <= 0:
        return ""
    return str(int(parsed))


def _landing_freshness(store: LandingStore, source: str) -> tuple[int, datetime | None, str | None]:
    keys = store.list_parquet(source)
    n = 0
    last: datetime | None = None
    snap: str | None = None
    for key in keys:
        meta = _read_manifest(store, key)
        if meta is not None:
            n += int(meta.get("rows") or 0)
            written = parse_datetime(meta.get("written_at"))
            if written is not None and (last is None or written > last):
                last = written
                snap = str(meta.get("sha256") or Path(key).stem)
            continue
        n += store.read_parquet(key).height
    return n, last, snap


def _read_manifest(store: LandingStore, parquet_key: str) -> dict | None:
    manifest_key = parquet_key.removesuffix(".parquet") + ".manifest.json"
    if not store.exists(manifest_key):
        return None
    raw = json.loads(store.get(manifest_key))
    if not isinstance(raw, dict):
        return None
    return raw


def _ch(settings: Settings):
    parsed = urlparse(settings.clickhouse_url)
    return clickhouse_connect.get_client(
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 8123,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )


def _f(value):
    return float(value) if value is not None else None


def _split_sql(sql: str) -> list[str]:
    parts = []
    buf = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
        if line.strip().endswith(";"):
            stmt = "\n".join(buf).strip().rstrip(";")
            if stmt:
                parts.append(stmt)
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "infra" / "postgres" / "01_compras.sql").exists():
            return p
    raise RuntimeError("infra/postgres/01_compras.sql not found")
