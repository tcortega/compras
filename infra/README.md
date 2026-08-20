# Infra

Local stack for Phase 1.

Copy `.env.example` to `.env` in this directory, then run `docker compose up -d`.

Services: Postgres 16, ClickHouse, MinIO, Meilisearch, Dagster webserver, Dagster daemon.

Landing is immutable content-hashed parquet under MinIO bucket `compras-landing`, partitioned `source/date=YYYY-MM-DD`.

E2E a user would run after the warehouse is up:

```
pip install -e ingest
export POSTGRES_DSN=postgresql://compras:compras@127.0.0.1:5432/compras
export CLICKHOUSE_URL=http://127.0.0.1:8123
export LANDING_URI=$PWD/.e2e-landing
python -m compras_ingest.e2e
```

CI runs that same E2E against service containers.

Python never calls C#.

Detector rows stay in `flag` with `state=detected`.
