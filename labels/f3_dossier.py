"""F3 Volta Redonda 2024 internal dossier checks.

Fixture-safe. Does not contact hosts. Does not run a detector.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("ingest", "normalize", "detect"):
    _p = str(_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from compras_ingest.cpf import assert_no_raw_cpf

DIR_NAME = "f3-volta-redonda-2024"
EXPECTED_IDS = (
    "4500680700113202400020",
    "9277610590104202400016",
    "4500680590077202400098",
    "4500680590126202400008",
    "9268500590078202400042",
    "4500680590045202400004",
    "4500680590104202400074",
    "4500680700113202400010",
    "4500680700118202400006",
)
EXPECTED_RANKS = (9, 11, 43, 50, 58, 59, 83, 85, 100)
SIGNAL_COLS = (
    "id_compra_item",
    "rank",
    "b1",
    "b2",
    "f1",
    "b1_evidence_url",
    "b2_evidence_url",
    "f1_evidence_url",
    "cpf_masked",
)
B1_KINDS = frozenset({"", "sanctioned_ceis_cnep"})
B2_KINDS = frozenset({"", "cnpj_age", "cnpj_age_info"})
F1_KINDS = frozenset({"", "shared_qsa_partner", "shared_address", "shared_phone", "shared_email"})
PHASE0_LABELS_HEADER = "rank,id_compra,id_compra_item,ID_contratacao_PNCP,numero_item,label,evidence_url,notes"
_DIGIT_RUN = re.compile(r"\d{11,}")
_EM = re.compile(r"\u2014|\u2013")
_CPF_MASK = re.compile(r"^\*\*\*\.\d{3}\.\d{3}-\*\*$")


def dossier_dir(root: Path) -> Path:
    return root / "labels" / DIR_NAME


def phase0_untouched(root: Path) -> None:
    precision = json.loads((root / "labels" / "precision.json").read_text(encoding="utf-8"))
    if precision.get("n_real") != 9 or precision.get("precision_real") != 0.09:
        raise SystemExit("Phase 0 precision.json was rewritten")
    if precision.get("n_unit_error") != 9 or precision.get("n_spec_difference") != 35 or precision.get("n_data_error") != 47:
        raise SystemExit("Phase 0 precision mix was rewritten")
    cov = json.loads((root / "labels" / "catmat-coverage.json").read_text(encoding="utf-8"))
    if cov.get("percent_coded") != 81.75:
        raise SystemExit("Phase 0 catmat-coverage.json was rewritten")
    if cov.get("n_items") != 5463:
        raise SystemExit("Phase 0 catmat n_items was rewritten")
    header = (root / "labels" / "labels.csv").read_text(encoding="utf-8").splitlines()[0]
    if header != PHASE0_LABELS_HEADER:
        raise SystemExit("Phase 0 labels.csv header was rewritten")
    first = (root / "labels" / "outliers-top100.csv").read_text(encoding="utf-8").splitlines()[1]
    if "92776105900292024" not in first:
        raise SystemExit("Phase 0 outliers-top100.csv was rewritten")


def real_ids_from_labels(root: Path) -> list[str]:
    path = root / "labels" / "labels.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    got = [r["id_compra_item"] for r in rows if r.get("label") == "real"]
    if got != list(EXPECTED_IDS):
        raise SystemExit(f"labels.csv real ids {got} != expected {list(EXPECTED_IDS)}")
    ranks = [int(r["rank"]) for r in rows if r.get("label") == "real"]
    if ranks != list(EXPECTED_RANKS):
        raise SystemExit(f"labels.csv real ranks {ranks} != expected {list(EXPECTED_RANKS)}")
    return got


def _no_raw_cpf_text(text: str, where: str) -> None:
    assert_no_raw_cpf([text])
    for match in _DIGIT_RUN.finditer(text):
        token = match.group(0)
        if len(token) == 14:
            continue
        if len(token) >= 17:
            continue
        raise SystemExit(f"{where} has a digit run that is not a CNPJ or item id: len={len(token)}")
    if _EM.search(text):
        raise SystemExit(f"{where} has an em dash or en dash")


def check_manifest(path: Path, ids: list[str]) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise SystemExit("manifest.json is not an object")
    got = list(manifest.get("id_compra_item") or [])
    if got != ids:
        raise SystemExit(f"manifest ids {got} != labels real {ids}")
    if str(manifest.get("municipio") or "") != "Volta Redonda":
        raise SystemExit("manifest municipio is not Volta Redonda")
    if str(manifest.get("ibge") or "") != "3306305":
        raise SystemExit("manifest ibge is not 3306305")
    if str(manifest.get("uf") or "") != "RJ":
        raise SystemExit("manifest uf is not RJ")
    if int(manifest.get("year") or 0) != 2024:
        raise SystemExit("manifest year is not 2024")
    if manifest.get("public_flag") is not False:
        raise SystemExit("manifest must set public_flag false")
    if manifest.get("explorer_dto") is not False:
        raise SystemExit("manifest must set explorer_dto false")
    methods = manifest.get("methods") or {}
    if "b1" not in methods or "b2" not in methods or "f1" not in methods:
        raise SystemExit("manifest methods missing b1/b2/f1")
    sources = manifest.get("official_sources") or []
    if not isinstance(sources, list) or len(sources) < 4:
        raise SystemExit("manifest official_sources missing")
    if not manifest.get("git_sha"):
        raise SystemExit("manifest missing git_sha")
    _no_raw_cpf_text(json.dumps(manifest, ensure_ascii=False), "manifest.json")
    return manifest


def check_signals(path: Path, ids: list[str]) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if list(rows[0].keys()) != list(SIGNAL_COLS) if rows else True:
        header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
        if header != list(SIGNAL_COLS):
            raise SystemExit(f"signals.csv header {header} != {list(SIGNAL_COLS)}")
    if len(rows) != 9:
        raise SystemExit(f"signals.csv has {len(rows)} rows, want 9")
    got = [r["id_compra_item"] for r in rows]
    if got != ids:
        raise SystemExit(f"signals.csv ids {got} != labels real {ids}")
    for row in rows:
        if row.get("b1") not in B1_KINDS:
            raise SystemExit(f"{row['id_compra_item']} b1 is not a known kind")
        if row.get("b2") not in B2_KINDS:
            raise SystemExit(f"{row['id_compra_item']} b2 is not a known kind")
        f1 = row.get("f1") or ""
        kinds = [p for p in f1.split("|") if p]
        if f1 and any(kind not in F1_KINDS or kind == "" for kind in kinds):
            raise SystemExit(f"{row['id_compra_item']} f1 is not a known kind")
        cpf = row.get("cpf_masked") or ""
        if cpf and not _CPF_MASK.match(cpf):
            raise SystemExit(f"{row['id_compra_item']} cpf_masked is not the ingest mask")
        _no_raw_cpf_text(",".join(row.values()), f"signals.csv {row['id_compra_item']}")
    return rows


def check_cases(folder: Path, ids: list[str]) -> None:
    for cid in ids:
        path = folder / f"{cid}.md"
        if not path.exists():
            raise SystemExit(f"missing case file {path}")
        text = path.read_text(encoding="utf-8")
        if len(text) < 400:
            raise SystemExit(f"{path.name} is too short for a dossier")
        if cid not in text:
            raise SystemExit(f"{path.name} missing its id")
        if "Volta Redonda" not in text:
            raise SystemExit(f"{path.name} missing municipio")
        if "3306305" not in text:
            raise SystemExit(f"{path.name} missing IBGE")
        if "not a public flag" not in text.lower() and "not a public alert" not in text.lower():
            raise SystemExit(f"{path.name} missing internal-only framing")
        if "surviving price anomaly" not in text:
            raise SystemExit(f"{path.name} missing real-means-anomaly framing")
        if "B1" not in text or "B2" not in text or "F1" not in text:
            raise SystemExit(f"{path.name} missing the cross-signal table")
        if "fraude" in text.lower() or "corrupt" in text.lower():
            raise SystemExit(f"{path.name} has accusatory copy")
        _no_raw_cpf_text(text, path.name)


def check_rollup(path: Path, ids: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    if "Volta Redonda" not in text or "3306305" not in text:
        raise SystemExit("rollup.md missing municipio")
    for cid in ids:
        if cid not in text:
            raise SystemExit(f"rollup.md missing {cid}")
    if "TCU 297/2009" not in text or "1.793/2011" not in text or "2.803/2016" not in text:
        raise SystemExit("rollup.md missing TCU shared-partner citations")
    if "surviving price anomaly" not in text:
        raise SystemExit("rollup.md missing real-means-anomaly framing")
    if "not a public flag" not in text.lower() and "not a public alert" not in text.lower():
        raise SystemExit("rollup.md missing internal-only framing")
    if "precision_real" in text and "0.63" in text:
        raise SystemExit("rollup.md rewrote Phase 0 precision")
    _no_raw_cpf_text(text, "rollup.md")


def e2e_check(root: Path | None = None) -> None:
    root = root or _ROOT
    phase0_untouched(root)
    ids = real_ids_from_labels(root)
    folder = dossier_dir(root)
    if not folder.is_dir():
        raise SystemExit(f"missing {folder}")
    check_manifest(folder / "manifest.json", ids)
    check_signals(folder / "signals.csv", ids)
    check_cases(folder / "cases", ids)
    check_rollup(folder / "rollup.md", ids)
    blobs = []
    for path in folder.rglob("*"):
        if path.is_file():
            blobs.append(path.read_text(encoding="utf-8"))
    assert_no_raw_cpf(blobs)
    print(f"f3 e2e ok dir={folder.name} n={len(ids)}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="F3 Volta Redonda 2024 dossier check")
    p.add_argument("--check", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        e2e_check(_ROOT)
        return 0
    raise SystemExit("use --check")


if __name__ == "__main__":
    raise SystemExit(main())
