"""Fetch PNCP item + resultado JSON for the A3 blind sample."""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import httpx

from compras_ingest.official import PNCP_API_BASE, USER_AGENT

ROOT = Path(__file__).resolve().parents[1]
A3 = ROOT / "labels" / "a3-bauru-2024"
OUT = A3 / "pncp-evidence.jsonl"
INTERVAL_S = 1.0


def parse_pncp(pncp: str, item_no: str) -> tuple[str, str, str, str]:
    left, ano = pncp.split("/")
    cnpj, _mid, seq = left.split("-")
    return cnpj, ano, str(int(seq)), str(int(item_no))


def main() -> int:
    rows = list(csv.DictReader((A3 / "sample-before.csv").open(encoding="utf-8")))
    done: set[str] = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["id_compra_item"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    last = 0.0
    with httpx.Client(timeout=httpx.Timeout(45.0, connect=15.0), headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, follow_redirects=True) as client, OUT.open("a", encoding="utf-8") as fh:
        for i, row in enumerate(rows, start=1):
            rid = row["id_compra_item"]
            if rid in done:
                print(f"skip {i} {rid}", flush=True)
                continue
            try:
                cnpj, ano, seq, n = parse_pncp(row["ID_contratacao_PNCP"], row["numero_item"])
            except Exception as exc:
                rec = {"id_compra_item": rid, "error": f"parse {exc}", "item": None, "resultados": None}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                print(f"parse-fail {i} {rid}", flush=True)
                continue
            item_url = f"{PNCP_API_BASE}/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens/{n}"
            res_url = f"{item_url}/resultados"
            now = time.monotonic()
            wait = INTERVAL_S - (now - last)
            if wait > 0:
                time.sleep(wait)
            item_resp = client.get(item_url)
            last = time.monotonic()
            wait = INTERVAL_S - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            res_resp = client.get(res_url)
            last = time.monotonic()
            rec = {
                "id_compra_item": rid,
                "item_url": item_url,
                "resultados_url": res_url,
                "item_status": item_resp.status_code,
                "resultados_status": res_resp.status_code,
                "item": item_resp.json() if item_resp.headers.get("content-type", "").startswith("application/json") and item_resp.content else None,
                "resultados": res_resp.json() if res_resp.headers.get("content-type", "").startswith("application/json") and res_resp.content else None,
                "csv": {
                    "descricao": row["descricao"],
                    "unidade_medida": row["unidade_medida"],
                    "quantidade": row["quantidade"],
                    "valor_unitario_estimado": row["valor_unitario_estimado"],
                    "valor_unitario_resultado": row["valor_unitario_resultado"],
                    "valor_total": row["valor_total"],
                    "valor_total_resultado": row["valor_total_resultado"],
                    "evidence_url": row["evidence_url"],
                    "ID_contratacao_PNCP": row["ID_contratacao_PNCP"],
                    "numero_item": row["numero_item"],
                },
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"{i}/100 {rid} item={item_resp.status_code} res={res_resp.status_code}", flush=True)
    print(f"wrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
