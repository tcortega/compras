# Infra

Local stack for Phase 1 plus the Phase 2 explorer.

Copy `.env.example` to `.env` in this directory.

From this directory:

```
docker compose up --build --wait
```

That command starts Postgres 16, ClickHouse, MinIO, Meilisearch, Dagster webserver and daemon, the warehouse seed, the search-index sync, the C# API, and the Next.js explorer.

Both Dagster processes load `/app/ingest/workspace.yaml`.
`icc` is part of `docker compose up` and keeps container-to-container traffic on a stock Linux Docker engine.
The dockerd snippet this stack expects is `docker/daemon.json`.

The seed runs the existing Python ingest/normalize into Postgres and ClickHouse using the in-repo 2024 fixture of 159 municípios listed in `web/lib/copy.ts` `SLICE_MUNICIPIOS`.

Python never calls C#.
C# never runs a detector.

## URLs

- Explorer: http://127.0.0.1:3100
- API: http://127.0.0.1:5080
- Dagster: http://127.0.0.1:3000
- Postgres: 127.0.0.1:5432
- ClickHouse HTTP: http://127.0.0.1:8123
- MinIO API: http://127.0.0.1:9000
- MinIO console: http://127.0.0.1:9001
- Meilisearch: http://127.0.0.1:7700

`search-index` reads warehouse text into Meilisearch after the seed.
Python never calls C# for that job.
Document id is `{kind}_{entityId}` so the upsert is idempotent.
`/busca` uses `GET /api/busca` against Meilisearch when `MEILI_URL` is set.
The explorer talks to the compose API at `http://api:5080`, not the in-process stub.

A browser on the explorer home must show the published slice with `n`, UF (RJ, SP, RS, SC, MG, PR, BA, PE, GO, ES, PB, CE, MA, AL, or UF mista when mixed), trimestre, and metodologia.
Mixed UF coverage leaves uf empty.
It is not a national total.

## Prove

After the stack is up:

```
python3 prove.py
```

That hits served API list/get and the served web home.
It fails if stub data is used while `API_BASE_URL` points at the API.
It fails if public flag fields leak.

Landing is immutable content-hashed parquet under MinIO bucket `compras-landing`, partitioned `source/date=YYYY-MM-DD`.
TCE-SP participant proposals land internally and are not read by the explorer.
TCE-RS LicitaCon participant proposals land internally and are not read by the explorer.
CGU CEIS/CNEP sanction lists land internally and are not read by the explorer.

Host pipeline E2E against the same warehouse, after the stack is up:

```
pip install -e ../ingest
export POSTGRES_DSN=postgresql://compras:compras@127.0.0.1:5432/compras
export CLICKHOUSE_URL=http://127.0.0.1:8123
export CLICKHOUSE_USER=compras
export CLICKHOUSE_PASSWORD=compras
export CLICKHOUSE_DATABASE=compras
export LANDING_URI=$PWD/../.e2e-landing
python -m compras_ingest.e2e
```

CI runs the host pipeline E2E and this compose prove.

Detector rows stay in `flag` with `state=detected`.
`GET /api/internal/flags` lists those facts.
The explorer does not link that route.
Receita adjacency rows stay in `fornecedor_adjacency`.
The explorer does not read that table.
