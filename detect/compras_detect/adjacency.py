from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import polars as pl

from compras_ingest.cpf import assert_no_raw_cpf, is_cnpj, is_cpf, mask_cpf
from compras_normalize.text import fold

KIND_PARTNER = "shared_qsa_partner"
KIND_ADDRESS = "shared_address"
KIND_PHONE = "shared_phone"
KIND_EMAIL = "shared_email"
KINDS = (KIND_PARTNER, KIND_ADDRESS, KIND_PHONE, KIND_EMAIL)

SCHEMA = {
    "kind": pl.String,
    "leftCnpj": pl.String,
    "rightCnpj": pl.String,
    "evidence": pl.String,
    "snapshot_id": pl.String,
    "methodology_version": pl.String,
}


def build_adjacencies(
    estabelecimentos: pl.DataFrame,
    socios: pl.DataFrame,
    snapshot_id: str,
    methodology_version: str,
) -> pl.DataFrame:
    """Undirected edges from landed Receita frames. CPF stays masked. Not a finding."""
    snap = str(snapshot_id or "")
    meth = str(methodology_version or "")
    estab_rows = list(_as_rows(estabelecimentos))
    socio_rows = list(_as_rows(socios))
    by_basico = _cnpjs_by_basico(estab_rows)
    rows = [
        *_partner_edges(socio_rows, by_basico),
        *_attribute_edges(estab_rows, KIND_ADDRESS, _address_key, "address"),
        *_attribute_edges(estab_rows, KIND_PHONE, None, "phone", keys_of=_phones),
        *_attribute_edges(estab_rows, KIND_EMAIL, _email_key, "email"),
    ]
    out = []
    for row in rows:
        evidence = mask_cpf(str(row["evidence"]))
        assert_no_raw_cpf([evidence, row["leftCnpj"], row["rightCnpj"]])
        out.append(
            {
                "kind": row["kind"],
                "leftCnpj": row["leftCnpj"],
                "rightCnpj": row["rightCnpj"],
                "evidence": evidence,
                "snapshot_id": snap,
                "methodology_version": meth,
            }
        )
    return pl.DataFrame(out) if out else pl.DataFrame(schema=SCHEMA)


def fixture_dir(root: Path | None = None) -> Path:
    base = root or _repo_root()
    path = base / "detect" / "fixtures" / "adjacency"
    if not path.exists():
        raise FileNotFoundError(f"adjacency golden fixture missing: {path}")
    return path


def load_expected(root: Path | None = None) -> dict:
    path = fixture_dir(root) / "expected.json"
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("adjacency expected.json is not an object")
    return payload


def _partner_edges(socios: list[dict], by_basico: dict[str, set[str]]) -> list[dict]:
    grouped: dict[str, set[str]] = defaultdict(set)
    meta: dict[str, str] = {}
    for row in socios:
        partner = _partner_key(row)
        if partner is None:
            continue
        key, partner_type = partner
        basico = _basico(row.get("cnpj_basico"))
        for cnpj in by_basico.get(basico, ()):
            grouped[key].add(cnpj)
        meta[key] = f"partner_key={key} partner_type={partner_type}"
    return _pairs(grouped, KIND_PARTNER, meta.get)


def _attribute_edges(
    estab: list[dict],
    kind: str,
    key_of,
    label: str,
    *,
    keys_of=None,
) -> list[dict]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for row in estab:
        cnpj = _cnpj14(row)
        if not cnpj:
            continue
        keys = keys_of(row) if keys_of else {_present(key_of(row))}
        for key in keys:
            if key:
                grouped[key].add(cnpj)
    return _pairs(grouped, kind, lambda key: f"{label}={key}")


def _pairs(grouped: dict[str, set[str]], kind: str, evidence_of) -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for key, cnpjs in grouped.items():
        ordered = sorted({c for c in cnpjs if c})
        for i, left in enumerate(ordered):
            for right in ordered[i + 1 :]:
                if left == right or left[:8] == right[:8]:
                    continue
                a, b = (left, right) if left < right else (right, left)
                token = (kind, a, b)
                if token in seen:
                    continue
                seen.add(token)
                rows.append(
                    {
                        "kind": kind,
                        "leftCnpj": a,
                        "rightCnpj": b,
                        "evidence": evidence_of(key),
                    }
                )
    return rows


def _partner_key(row: dict) -> tuple[str, str] | None:
    ident = str(row.get("identificador_de_socio") or "").strip()
    raw = str(row.get("cnpj_cpf_do_socio") or "").strip()
    if not raw:
        return None
    digits = "".join(c for c in raw if c.isdigit())
    masked = mask_cpf(raw)
    if ident == "1" or len(digits) == 14 or is_cnpj(raw):
        token = digits if len(digits) == 14 else _alnum(raw)
        return (token, "cnpj") if token else None
    if ident == "2" or is_cpf(raw) or _masked_cpf(masked):
        return (masked, "cpf") if _masked_cpf(masked) or is_cpf(raw) else None
    if len(digits) == 14:
        return digits, "cnpj"
    if _masked_cpf(masked):
        return masked, "cpf"
    return None


def _address_key(row: dict) -> str:
    street = fold(f"{row.get('tipo_logradouro') or ''} {row.get('logradouro') or ''}")
    numero = fold(row.get("numero"))
    cep = "".join(c for c in str(row.get("cep") or "") if c.isdigit())
    municipio = fold(row.get("municipio"))
    if not street or not (numero or cep):
        return ""
    return " ".join(part for part in (street, numero, cep, municipio) if part)


def _phones(row: dict) -> set[str]:
    return {
        key
        for key in (
            _phone_key(row.get("ddd1"), row.get("telefone1")),
            _phone_key(row.get("ddd2"), row.get("telefone2")),
        )
        if key
    }


def _phone_key(ddd, telefone) -> str:
    digits = "".join(c for c in f"{ddd or ''}{telefone or ''}" if c.isdigit())
    if not digits or is_cpf(digits):
        return ""
    return digits


def _email_key(row: dict) -> str:
    raw = fold(row.get("correio_eletronico"))
    if not raw or "@" not in raw:
        return ""
    return mask_cpf(raw)


def _cnpjs_by_basico(estab: list[dict]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for row in estab:
        cnpj = _cnpj14(row)
        if cnpj:
            out[cnpj[:8]].add(cnpj)
    return out


def _cnpj14(row: dict) -> str:
    direct = _alnum(row.get("cnpj"))
    if len(direct) == 14:
        return direct
    basico = _basico(row.get("cnpj_basico"))
    if not basico:
        return ""
    ordem = _alnum(row.get("cnpj_ordem")).zfill(4)[-4:]
    dv = _alnum(row.get("cnpj_dv")).zfill(2)[-2:]
    return f"{basico}{ordem}{dv}"


def _basico(value) -> str:
    token = _alnum(value)
    return token[:8].zfill(8) if token else ""


def _alnum(value) -> str:
    return "".join(c for c in str(value or "") if c.isalnum()).upper()


def _masked_cpf(value: str) -> bool:
    return value.startswith("***") and "-" in value


def _present(value: str | None) -> str:
    return value or ""


def _as_rows(df: pl.DataFrame) -> list[dict]:
    if df is None or df.is_empty():
        return []
    return list(df.iter_rows(named=True))


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "detect" / "fixtures").exists() and (p / "docs" / "CONTRACT.md").exists():
            return p
    return here.parents[2]
