# A3 Bauru 2024

This folder is the A3 sprint headline sample.
Municipio is Bauru, SP, IBGE 3506003, year 2024, municipal non-legislative COMPRA+ITEM.
Caxias do Sul was not needed because Bauru had 2652 priced items.
sample-before.csv is the blind labeler view and has no score, rank, or exclusion reason.
scores-before.csv holds rank and score keyed by the same ids.
labels.csv uses the Phase 0 columns after the blind pass.
precision-before.json is the BEFORE top-100 mix (42 real / 100).
precision-after.json is the AFTER anomaly_pool mix on already labeled rows (34 real / 74 labeled, 26 unresolved).
catmat-coverage.json is the exact integer catalog join on this municipio slice.
manifest.json records peer definition, official file URLs, A1/A2 versions, and which pool is before or after.
Phase 0 files under /labels remain the VR 2024 9 percent / 81.75 percent baseline.
The explorer was not changed.
No public flags were added.
Run `python3 labels/a3_sample.py --check` for the fixture-safe E2E.
