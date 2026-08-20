from __future__ import annotations

import sys

from compras_ingest.pipeline import run_compras_slice
from compras_ingest.settings import Settings
from compras_ingest.warehouse import fetch_counts, fetch_one_orgao, fetch_orgaos

SLICES = (
    ("29477000000180", "3306305", "RJ", "Volta Redonda"),
    ("28521748000159", "3303302", "RJ", "Niterói"),
    ("46137410000180", "3506003", "SP", "Bauru"),
    ("88830609000139", "4305108", "RS", "Caxias do Sul"),
    ("83169623000110", "4209102", "SC", "Joinville"),
    ("18431312000115", "3170206", "MG", "Uberlândia"),
    ("75771477000170", "4113700", "PR", "Londrina"),
)


def main() -> int:
    settings = Settings.from_env()
    result = run_compras_slice(settings)
    seen_ibge: set[str] = set()
    seen_uf: set[str] = set()
    for cnpj, ibge, uf, nome in SLICES:
        orgao = fetch_one_orgao(settings, cnpj)
        if orgao is None:
            raise SystemExit(f"missing {nome} orgao {cnpj}")
        if str(orgao.get("municipioIbge") or "") != ibge:
            raise SystemExit(f"{nome}: expected IBGE {ibge}, got {orgao.get('municipioIbge')}")
        if str(orgao.get("uf") or "") != uf:
            raise SystemExit(f"{nome}: expected UF {uf}, got {orgao.get('uf')}")
        seen_ibge.add(ibge)
        seen_uf.add(uf)
        print(f"orgao={orgao['cnpj']} ibge={orgao['municipioIbge']} uf={orgao['uf']}")
    if len(seen_ibge) < 7:
        raise SystemExit(f"warehouse missing published IBGE codes: {sorted(seen_ibge)}")
    if seen_uf != {"RJ", "SP", "RS", "SC", "MG", "PR"}:
        raise SystemExit(f"warehouse UF set is not RJ+SP+RS+SC+MG+PR: {sorted(seen_uf)}")
    landed = {(str(o.get("municipioIbge") or ""), str(o.get("uf") or "")) for o in fetch_orgaos(settings)}
    if landed != {
        ("3306305", "RJ"),
        ("3303302", "RJ"),
        ("3506003", "SP"),
        ("4305108", "RS"),
        ("4209102", "SC"),
        ("3170206", "MG"),
        ("4113700", "PR"),
    }:
        raise SystemExit(f"warehouse orgao set is not the published slice: {sorted(landed)}")
    counts = fetch_counts(settings)
    if counts["item"] < 1:
        raise SystemExit("warehouse has no items")
    if counts["orgao"] < 7:
        raise SystemExit(f"warehouse orgao count {counts['orgao']} < 7")
    print("seed ok")
    print(f"entities={result.entity_counts} facts={result.fact_rows} flags={result.flag_rows}")
    print(f"counts={counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
