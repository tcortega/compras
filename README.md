# compras

Brazilian public-procurement transparency platform.

Coverage is incomplete.
Every aggregate must show its coverage denominator (n comparables, UF, quarter).
This product does not claim national completeness.

Municipalities under 20,000 inhabitants have until 31 March 2027 to publish to PNCP.
Genuine national municipal coverage is not achievable before roughly 2027-2028.

See [PROJECT.md](docs/PROJECT.md) and [BUILD_SPEC.md](docs/BUILD_SPEC.md).

From `infra`, `docker compose up --build --wait` serves the explorer at http://127.0.0.1:3100 and the API at http://127.0.0.1:5080 against the 2024 warehouse slice (Volta Redonda and Niterói in RJ, Bauru in SP, Caxias do Sul in RS, Joinville in SC, Uberlândia in MG, Londrina in PR, Feira de Santana in BA, Caruaru in PE, Anápolis in GO, Vila Velha in ES, Campina Grande in PB, Caucaia in CE, Imperatriz in MA, Arapiraca in AL, Dourados in MS, Marabá in PA, Várzea Grande in MT, Ji-Paraná in RO, Parnamirim in RN, Cruzeiro do Sul in AC, Santana in AP, Rorainópolis in RR, Maringá in PR, Taubaté in SP, Cascavel in PR, Juiz de Fora in MG, Foz do Iguaçu in PR, Santa Maria in RS, Montes Claros in MG, Governador Valadares in MG, Canoas in RS, Lages in SC, Santarém in PA, Rio Verde in GO, Paulo Afonso in BA, São Lourenço da Mata in PE, Crato in CE, Ariquemes in RO, Colatina in ES, Castanhal in PA, Divinópolis in MG, Petrópolis in RJ).

Phase 0 is the hard start.
Do not build public flags until the precision number exists in `/labels`.
Nothing accusatory ships before 25 October 2026.

Layout:

- `/ingest` Python Dagster assets
- `/normalize` CATMAT and unit canonicalization
- `/detect` tier1 / tier2 / tier3
- `/api` C# ASP.NET Core
- `/web` Next.js
- `/infra` compose and terraform
- `/docs` methodology and specs
- `/labels` hand-labeled ground truth

Python never calls C#.
C# never runs a detector.
The warehouse is the only contract between them.
