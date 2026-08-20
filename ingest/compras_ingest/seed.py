from __future__ import annotations

import sys

from compras_ingest.pipeline import run_compras_slice
from compras_ingest.settings import Settings
from compras_ingest.warehouse import fetch_counts, fetch_one_orgao

ORGAO_CNPJ = "29477000000180"
IBGE = "3306305"
UF = "RJ"


def main() -> int:
    settings = Settings.from_env()
    result = run_compras_slice(settings)
    orgao = fetch_one_orgao(settings, ORGAO_CNPJ)
    if orgao is None:
        raise SystemExit(f"missing Volta Redonda orgao {ORGAO_CNPJ}")
    if str(orgao.get("municipioIbge") or "") != IBGE:
        raise SystemExit(f"expected IBGE {IBGE}, got {orgao.get('municipioIbge')}")
    if str(orgao.get("uf") or "") != UF:
        raise SystemExit(f"expected UF {UF}, got {orgao.get('uf')}")
    counts = fetch_counts(settings)
    if counts["item"] < 1:
        raise SystemExit("warehouse has no items")
    print("seed ok")
    print(f"orgao={orgao['cnpj']} ibge={orgao['municipioIbge']} uf={orgao['uf']}")
    print(f"entities={result.entity_counts} facts={result.fact_rows} flags={result.flag_rows}")
    print(f"counts={counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
