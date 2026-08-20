from __future__ import annotations

import hashlib
import json
import uuid

NS = uuid.UUID("6b1c0a7e-4d2f-4c91-9b3a-0f8e2d17a5c4")


def orgao_id(cnpj: str) -> str:
    return str(uuid.uuid5(NS, f"orgao:{cnpj}"))


def fornecedor_id(cnpj: str) -> str:
    return str(uuid.uuid5(NS, f"fornecedor:{cnpj}"))


def contratacao_id(pncp_id: str) -> str:
    return str(uuid.uuid5(NS, f"contratacao:{pncp_id}"))


def item_id(pncp_id: str, record_id: str) -> str:
    return str(uuid.uuid5(NS, f"item:{pncp_id}:{record_id}"))


def flag_id(item: str, kind: str, snapshot_id: str) -> str:
    return str(uuid.uuid5(NS, f"flag:{item}:{kind}:{snapshot_id}"))


def socio_id(cnpj: str, nome: str, cpf_masked: str | None, qualificacao: str | None) -> str:
    return str(uuid.uuid5(NS, f"socio:{cnpj}:{nome}:{cpf_masked or ''}:{qualificacao or ''}"))


def participante_id(licitacao_id: str, item_lote: str, participante: str, source: str) -> str:
    return str(uuid.uuid5(NS, f"participante:{source}:{licitacao_id}:{item_lote}:{participante}"))


def cobid_screen_id(kind: str, subject: str, snapshot_id: str) -> str:
    return str(uuid.uuid5(NS, f"cobid_screen:{kind}:{subject}:{snapshot_id}"))


def record_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
