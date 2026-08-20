# Infra

Local stack for Phase 1 plus the Phase 2 explorer.

Copy `.env.example` to `.env` in this directory.

From this directory:

```
docker compose up --build --wait
```

That command starts Postgres 16, ClickHouse, MinIO, Meilisearch, Dagster, the warehouse seed, the C# API, and the Next.js explorer.

The seed runs the existing Python ingest/normalize into Postgres and ClickHouse using the in-repo 2024 fixture: Volta Redonda RJ 3306305, Niterói RJ 3303302, Bauru SP 3506003, Caxias do Sul RS 4305108, Joinville SC 4209102, Uberlândia MG 3170206, Londrina PR 4113700, Feira de Santana BA 2910800, Caruaru PE 2604106, Anápolis GO 5201108, Vila Velha ES 3205200, Campina Grande PB 2504009, Caucaia CE 2303709, Imperatriz MA 2105302, Arapiraca AL 2700300, Dourados MS 5003702, Marabá PA 1504208, Várzea Grande MT 5108402, Ji-Paraná RO 1100122, Parnamirim RN 2403251, Cruzeiro do Sul AC 1200203, Santana AP 1600600, and Rorainópolis RR 1400472.

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
