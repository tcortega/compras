# Explorer API

ASP.NET Core 8 read API for canonical procurement entities in Postgres.

The explorer searches, browses, and drills into orgaos, fornecedores, contratacoes, and items.

Every aggregate returns a coverage denominator (`n`, `uf`, `quarter`, `methodologyVersion`).

Coverage is incomplete and is never presented as a national total.

Publication and right-of-reply live on `/api/internal/*` and are not explorer routes.

Flags stay internal and are framed as an indicio requiring verification.

Explorer reads Postgres.

Compose (`infra/`) seeds the 2024 warehouse (Volta Redonda, Niterói, Bauru, Caxias do Sul, Joinville, Uberlândia, Londrina) via Python, then serves this API on http://127.0.0.1:5080.

The warehouse schema is the contract.
This process does not apply EF migrations against that schema unless `App:ApplyMigrations` is true.

ClickHouse.Client is packaged for later analytical reads.

Time is NodaTime only.
