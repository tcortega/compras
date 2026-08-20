# Explorer API

ASP.NET Core 8 read API for canonical procurement entities in Postgres.

The explorer searches, browses, and drills into orgaos, fornecedores, contratacoes, and items.

Every aggregate returns a coverage denominator (`n`, `uf`, `quarter`, `methodologyVersion`).

Coverage is incomplete and is never presented as a national total.

Publication and right-of-reply live on `/api/internal/*` and are not explorer routes.

Flags stay internal and are framed as an indicio requiring verification.

Explorer reads Postgres.

ClickHouse.Client is packaged for later analytical reads.

Time is NodaTime only.
