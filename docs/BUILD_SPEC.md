# Brazilian Procurement Transparency Platform - Build Spec

Version 0.1.
Target consumer: autonomous coding agent.
Written to be executed phase by phase with hard gates between phases.

## 0. Do we have everything?

Architecture, data sources, legal frame: yes.
Three numbers are still unknown and cannot be researched, only measured:

1. Precision of naive price-anomaly detection on real municipal data.
2. Percentage of PNCP item records carrying valid CATMAT/CATSER codes vs free text.
3. Which state TCEs actually expose bid-participant proposal values, field by field.

All three are Phase 0 outputs.
Do not design around assumed values.

## 1. Stack

Locked. Do not substitute without a written reason.

| Layer | Choice | Why |
|---|---|---|
| Ingest / normalize / detect | Python 3.12 + Dagster | Asset lineage is a legal requirement here, not a nicety |
| Dataframes | Polars | Rust core, no pandas |
| Local analytics | DuckDB | Dev against parquet, same files as prod |
| Warehouse | ClickHouse | 10^8 item rows, cheap scans, single-box viable |
| Canonical entities + app state | Postgres 16 | Constraints, audit history, relational |
| Search | Meilisearch | Citizen-facing free-text over item descriptions |
| API | C# / ASP.NET Core 8 minimal APIs | User preference, fine here |
| ORM | EF Core to Postgres | ClickHouse.Client for analytical reads |
| Frontend | Next.js + React | Entity pages prerendered, ISR, CDN |
| Object storage | S3-compatible | Immutable landing zone, parquet, content-hashed |
| LLM | Batch API, dedupe first | Extraction and catalog matching only, never judgment |

Hard rule on the seam.
Python never calls C#.
C# never runs a detector.
The warehouse is the only contract between them.
This lets the entire pipeline be rerun or rewritten without touching the app, which will happen many times as normalization improves.

## 2. Data sources

Ranked by ingest priority.
Start at 1, do not skip ahead.

### Tier A - bulk, fast, start here

1. **Compras.gov.br bulk CSVs**
   - `https://repositorio.dados.gov.br/seges/comprasgov/` - annual/monthly/daily, contratações and items
   - `https://repositorio.dados.gov.br/seges/comprasnet_contratos/` - contracts, explicit mass download
   - Coverage: federal + roughly 563 state entities + 1,267 municipalities
   - This is the single highest-value source. It gives item-level detail with CATMAT codes and requires no scraping.

2. **OCP OCDS republished feed** - `https://data.open-contracting.org/en/publication/157`
   - Same underlying data, normalized to OCDS schema, daily
   - Use as schema reference and cross-check, not primary

3. **CATMAT / CATSER catalogs** - `https://dadosabertos.compras.gov.br/swagger-ui/index.html`, Módulo Material
   - Bulk consolidated file also on dados.gov.br
   - Needed before any normalization work starts

4. **Receita Federal CNPJ full dump**
   - Partners, addresses, CNAE, opening dates
   - Graph substrate for all Tier 2 detectors

### Tier B - slow, needed for coverage

5. **PNCP consulta API** - `https://pncp.gov.br/api/consulta`, Swagger at `/swagger-ui/index.html`
   - Only route for entities not on Compras.gov.br
   - No bulk export exists as of mid-2026 despite the 2024 Transparência Brasil recommendation
   - Constraints: page size 50 for contratações, 100 instrumentos, 500 atas/contratos/PCA
   - `codigoModalidadeContratacao` is mandatory, so iterate modality x date x page
   - No published rate limit, but gov.br throttles per IP. Use 1s spacing minimum, exponential backoff, resumable cursors.
   - Expect multi-week wall clock and repeated server failures. Transparência Brasil needed 10 days for a partial extraction.

6. **State TCEs** - the only source of bid participants and proposed values
   - Federal DW-SIASG carried this until 2023, current Compras API does not
   - Priority order: TCE-SP (Fase IV data cube, from Jan 2018), TCE-RS (LicitaCon), TCE-PR, TCE-PE, TCE-RJ (SIGFIS), TCM-SP
   - Verify participant fields per portal. Do not assume.

### Tier C - enrichment

7. **Portal da Transparência CGU** - `https://portaldatransparencia.gov.br/download-de-dados`, bulk CSVs, plus CEIS/CNEP sanction lists
8. **TSE dados abertos** - candidates, donors, declared patrimony. Only legitimate bridge from spending to people.
9. **Querido Diário** - municipal diários oficiais, covers small municipalities exempt from PNCP until 31 Mar 2027
10. **Painel de Preços / Banco de Preços em Saúde** - reference price baselines

## 3. Coverage reality

State this publicly on day one.
Do not claim national completeness.

- Lei 8.666/93 revoked 30 Dec 2023, so 2024 is the first year of centralized municipal item-level data.
- Municipalities under 20,000 inhabitants have until 31 Mar 2027 to publish to PNCP (art. 176). Until then diário oficial only.
- TCU Acórdão 53/2025 found 86.4% of PNCP records carry inconsistencies, up from 73.3%. Quality is degrading, not improving.
- Genuine national municipal coverage is not achievable before roughly 2027-2028.

Design implication.
Every aggregate must display its coverage denominator.
"41 comparable purchases in SP, Q2/2026" not "the median price in Brazil".

## 4. Detectors

Build in this order.
Precision descends as you go down.

### Tier 1 - deterministic, factual, no inference

Ship these first. They are arithmetic, not accusation.

- **qty x unit_price != total_value** - data entry error. Catches a large share of false "R$500 pencil" cases. Run this before anything else.
- **Fracionamento** - same órgão, same CATMAT, repeated purchases clustering under the dispensa threshold within a fiscal year window. Art. 75 §1 aggregates same-object spend annually.
- **CNPJ age** - supplier opened under 90 days before winning.
- **CNAE mismatch** - registered activity unrelated to what was sold.
- **Sanctioned supplier** - join against CEIS/CNEP.
- **Retroactive edit** - record content hash changed after publication. Free from the immutable landing zone. Nobody else surfaces this.

### Tier 2 - graph

Requires Receita CNPJ dump and, for the strongest signals, TCE participant data.

- Shared address / partner / phone / contador / IP across nominally competing bidders
- Vendor concentration: one CNPJ wins over N% of an órgão's dispensas
- Bid rotation among a fixed CNPJ set
- Supplier following a specific servidor across órgãos
- CADE-validated screens: low bid variance, negative skew, high price correlation, cover bidding, bid suppression

### Tier 3 - price anomaly

Lowest precision. Gate hardest.

- Peer group only: same CATMAT + same UF + same quarter + similar quantity band
- Robust statistics: median and MAD, never mean and sigma
- Report delta with n, never a verdict

### Legal caveats baked into detector output

- Fracionamento requires dolo específico in court. Statistical splitting is a lead, not proof.
- TCU jurisprudence (Acórdãos 297/2009, 1.793/2011, 2.803/2016) holds shared partners between bidders is not per se illegal. Irregular mainly in convite/dispensa or where competition is demonstrably harmed. Require multi-signal corroboration.

## 5. Trust score

Never ask the LLM for its own confidence.
Compose from measurable inputs:

```
score = f(
  catmat_match_quality,    # exact code / fuzzy / none
  unit_parse_confidence,   # parsed / inferred / unknown
  peer_group_n,            # 3 comparables vs 400
  deviation_magnitude,     # MAD units
  source_completeness,     # full contract vs partial record
  quantity_field_sanity    # qty * unit_price == total?
)
```

Every input is independently checkable against the labeled set.
LLM contributes only catmat_match_quality and extraction confidence.

Set a publish threshold.
Everything below stays in the DB, invisible.
This threshold is the single most important knob in the system.

## 6. Publication state machine

Enforced in Postgres. No flag reaches the public without traversing this.

```
detected -> internal_review -> notified -> published -> {resolved, retracted}
```

Rules:

- **notified** state holds 7 days minimum before publish. The órgão gets the flag before the public does.
- Replies publish unedited, adjacent to the flag, same visual weight.
- Unanswered flags display "no response as of [date]". That line is more damning than any accusation and is a statement of fact.
- Resolved flags stay visible, marked resolved. Visible corrections build the credibility that makes unresolved flags land.
- Every published record carries `snapshot_id` + `methodology_version` + the pinned query. Reproducible by anyone. This is simultaneously the credibility story and the legal defense.
- Per-entity suspend flag for takedown orders. Versioned publications so you can prove what was shown and when.

## 7. Framing rules

Non-negotiable. Applies to every string rendered to the public.

- Publish the delta and the source document, never the label.
- Rank órgãos and fornecedores, never individuals. Institutional attribution is direct and factual. Let the user drill from órgão to who signed, and make the inference themselves.
- No party-level aggregation. Aggregating over municipality size, region, and state capacity and calling the residual corruption is not a finding, and it hands critics a permanent correct line of attack.
- Word every flag as "indício requiring verification", following Serenata and ABRAJI Publique-se precedent.
- Mask CPF at ingest (`***.456.789-**`). Never store raw. ANPD guidance permits naming public agents but requires proportionality and minimization.

Template:

> Órgão X paid R$487.00/unit for CATMAT 123456 on [date].
> Median across 41 comparable purchases in SP, Q2/2026: R$3.20.
> Source: PNCP contract #####.
> Reply from órgão: [none as of DD/MM/YYYY].

## 8. Roadmap

### Phase 0 - the gate (week 1)

Nothing else starts until this completes.

1. Pull Compras.gov.br bulk CSVs for one mid-size município, one year.
2. Run naive price-outlier detection. Take top 100.
3. Hand-check each against source contracts. Label: real / unit error / spec difference / data error.
4. Measure CATMAT coverage percentage on the same slice.
5. Probe TCE-SP and TCE-RS for participant-level proposal fields.

**Gate:** if real-fraud precision is under 20%, Tier 3 detectors do not ship publicly in Phase 2 or 3.
The 100 labeled items become the seed of the permanent labeled set.

### Phase 1 - pipeline (weeks 2-8)

- Dagster assets for Tier A sources 1-4
- Immutable landing, content-hashed, parquet, partitioned by source/date
- Item normalization: free text -> CATMAT -> canonical unit -> price per base unit
- Benchmark to beat: Transparência Brasil's medicine classifier hit 98% classification accuracy and 86% correct-item identification against 1,000 manually labeled items
- unidadeMedida normalization table (it is effectively free text, expect wide variance)
- Tier 1 detectors running, output internal only
- No public surface

### Phase 2 - public explorer (months 3-6)

- Search, browse, drill down. No scoring, no flags, no ranking.
- Near-zero legal surface, immediately useful, and it is the exact pipeline needed anyway
- Publication state machine and right-of-reply infrastructure built and tested, even though nothing is flagged yet
- Methodology doc published and versioned
- Prerendered entity pages behind CDN. Assume a two-order-of-magnitude traffic spike within ten minutes if it lands.

### Phase 3 - Tier 1 flags + TCE integration (months 6-12)

- Turn on Tier 1 deterministic detectors publicly, subject to Phase 0 gate
- Integrate TCE-SP, TCE-RS, TCE-PR for participant data
- Build Tier 2 graph detectors, internal only initially
- PNCP API backfill running continuously in background for non-Compras entities

### Phase 4 - national best effort (months 12-18)

- Remaining TCEs, Querido Diário for exempt small municipalities
- Tier 2 public, subject to precision gate
- Tier 3 public only if Phase 0 and ongoing sampling justify it

### Election constraint

First round 4 Oct 2026, runoff 25 Oct 2026.
Nothing accusatory ships before 25 Oct 2026.
The Phase 2 explorer may ship during the period; flags and rankings may not.

Rationale, not caution.
Lei 9.504/97 art. 58 gives 72-hour right-of-reply decisions with 24-hour internet appeal windows under Res.-TSE 23.608/2019.
ABRAJI documents politicians routinely using these to force removals.
TSE jurisprudence protects factual sourced criticism (REspe 0600057-54/MA), so accurate work is defensible, but the response clock is faster than a small team can serve while also debugging a new pipeline.

## 9. Ongoing gates

Re-evaluate at each phase boundary.

- Item classifier precision under 90% on a fresh labeled sample -> Tier 3 stays internal
- Any published signal exceeding its FP threshold on sampled review -> suppress that signal, retrain
- MGI ships a true national PNCP bulk export -> re-prioritize PNCP as primary, drop scraping effort
- After 31 Mar 2027 -> reassess municipal coverage completeness before making any national claim

## 10. Repo layout

```
/ingest       python, dagster assets, one module per source
/normalize    python, catmat matching, unit canonicalization
/detect       python, tier1/ tier2/ tier3/
/api          C# aspnet core
/web          next.js
/infra        docker-compose, terraform
/docs         methodology.md - public, versioned, stamped on every flag
/labels       the hand-labeled ground truth set, version controlled
```

## 11. Agent conventions

Applies to all generated code.

- Extremely concise. Sacrifice grammar for concision in comments and docs.
- Never use em dash. Use plain dash.
- In technical decisions do not weight dev cost. Prefer quality, simplicity, robustness, scalability, long-term maintainability.
- Fix bugs by first reproducing E2E as an end user would.
- Be pixel-perfect and picky about UI. Fix anything that looks off.
- Fix any lint failure, test failure, or flakiness on sight, even if unrelated to the task.
- Never add the agent as co-author in commit messages.
- Never manually edit CHANGELOG.md or auto-generated files.
- When writing or editing long Markdown, put each full sentence on its own line.

## 12. Open items requiring a human

- Brazilian counsel on retainer, specialist in eleitoral and digital, before any public flag ships.
- One retired TCE auditor or procurement specialist as advisor. Worth more than any amount of compute. They will tell you in an afternoon which patterns are real fraud and which are boring administrative artifacts, and that knowledge is not in the data.
- 2-3 human labelers, ongoing. This is the input that produces the precision number.
- Funding structure decision: nonprofit with donors, or company with a revenue model that does not touch the ranking. The product's only asset is being believed, and the cap table will be scrutinized within a week of launch.
