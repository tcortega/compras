# PROJECT.md

Read this first. Then read BUILD_SPEC.md for the full technical plan.

What this is

A public data platform that aggregates Brazilian government procurement records - federal, state, and municipal - normalizes them to a comparable item level, and surfaces statistical anomalies and structural fraud patterns to citizens.

Brazil publishes procurement data by law but publishes it badly: scattered across incompatible systems, with free-text item descriptions, inconsistent units, and an 86.4% record inconsistency rate per TCU Acórdão 53/2025. The data is technically public and practically unusable. This project makes it usable.

Goals

Ingest and normalize procurement data into a single queryable item-level dataset with canonical units and catalog codes.

Let any citizen search what their city bought, from whom, for how much, and compare it to what comparable buyers paid.

Detect structural fraud patterns - contract splitting, shell suppliers, bidder collusion, price outliers - with measured precision, not asserted precision.

Make every published claim reproducible from an immutable snapshot and a versioned methodology.

Non-goals

Explicit. Do not build these even if they seem like natural extensions.

No politician ranking. Rank órgãos and fornecedores. Institutional attribution is factual and direct; individual attribution is a chain of inference with weak links.

No party-level aggregation. Aggregating over municipality size, region, and state capacity and calling the residual corruption is not a finding.

No accusatory language. Publish the delta and the source document. Never the label. Never "stealing", "fraud", or "corrupt" attached to a named entity.

No LLM price judgment. LLMs handle extraction, catalog matching, and document parsing. Statistics handles whether a price is anomalous.

No public flags before the measured precision gate passes. See BUILD_SPEC.md §8 Phase 0.

Why the design looks defensive

Prior art sets the bar. Operação Serenata de Amor analyzed 3M+ reimbursements, flagged 17,700 suspicions, filed 600+ complaints, and recovered R$50,569. That is the real conversion rate from "looks suspicious" to "confirmed wrong".

Most anomalies are not fraud. They are unit mismatches, spec differences, quantity typos, and registro-de-preços ceilings. A system that publishes raw outliers is wrong thousands of times in month one and loses credibility permanently.

The platform's only asset is being believed. Every design rule follows from protecting that.

Hard constraints

Coverage is incomplete and must be stated as such. Municipalities under 20,000 inhabitants are exempt from PNCP publication until 31 March 2027. Never claim national completeness. Always display the coverage denominator.

Bid participant data exists only in state TCE portals. It left the federal feed in 2023. Collusion detection depends on TCE integration, not PNCP.

CPF is masked at ingest. Never stored raw. Public agents may be named; their document numbers may not be published in full.

Every flag goes through the publication state machine. detected → internal_review → notified → published. The órgão is notified 7 days before the public sees anything, and its reply publishes unedited at equal visual weight.

Nothing accusatory ships before 25 October 2026. Brazilian general election is 4 October with a 25 October runoff. The read-only explorer may ship during this window. Flags may not.

Architecture in one paragraph

Python + Dagster ingests to an immutable content-hashed parquet landing zone, normalizes free-text items to CATMAT catalog codes and canonical units, and writes facts to ClickHouse and canonical entities to Postgres. A C# ASP.NET Core API reads from both and serves a Next.js frontend of prerendered entity pages behind a CDN. Python never calls C#, C# never runs a detector; the warehouse is the only contract between them, so the pipeline can be rerun or rewritten without touching the app.

Where to start

BUILD_SPEC.md §8 Phase 0. One município, one year, 100 hand-labeled anomalies. Do not build anything else until that precision number exists.
