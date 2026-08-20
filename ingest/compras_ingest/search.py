"""Sync warehouse text into Meilisearch. Factual fields only. No flags. No CPF."""

from __future__ import annotations

import sys
import time
from typing import Any

import httpx

from compras_ingest.settings import Settings
from compras_ingest.warehouse import fetch_all_items, fetch_fornecedores, fetch_orgaos

INDEX = "compras"
PRIMARY_KEY = "id"
KINDS = ("item", "orgao", "fornecedor")
SEARCHABLE = ["text"]
FILTERABLE = ["kind"]
DISPLAYED = ["id", "kind", "entityId", "text"]
CHUNK = 1000
TASK_WAIT_S = 60
BANNED_KEYS = (
    "flag",
    "score",
    "cpf",
    "adjacenc",
    "shared_qsa",
    "shared_partner",
    "shared_address",
    "shared_phone",
    "shared_email",
)


def main() -> int:
    summary = sync_search_index(Settings.from_env())
    print(
        f"search-index ok index={INDEX} docs={summary['docs']} "
        f"items={summary['items']} orgaos={summary['orgaos']} fornecedores={summary['fornecedores']}"
    )
    return 0


def sync_search_index(settings: Settings) -> dict[str, int]:
    if not settings.meili_url:
        raise SystemExit("MEILI_URL unset. Search sync needs Meilisearch.")
    docs = list_documents(settings)
    _assert_factual(docs)
    with _client(settings) as client:
        _ensure_index(client)
        _wait_task(client, _patch_json(client, f"/indexes/{INDEX}/settings", {
            "searchableAttributes": SEARCHABLE,
            "filterableAttributes": FILTERABLE,
            "displayedAttributes": DISPLAYED,
        }))
        live_ids = {str(doc["id"]) for doc in docs}
        for batch in _chunks(docs, CHUNK):
            _wait_task(client, _put_json(client, f"/indexes/{INDEX}/documents?primaryKey={PRIMARY_KEY}", batch))
        stale = _document_ids(client) - live_ids
        if stale:
            _wait_task(client, _post_json(client, f"/indexes/{INDEX}/documents/delete-batch", sorted(stale)))
        stats = _get_json(client, f"/indexes/{INDEX}/stats")
        indexed = int(stats.get("numberOfDocuments") or 0)
        if indexed != len(docs):
            raise SystemExit(f"meili docs {indexed} != warehouse {len(docs)}")
    counts = {kind: sum(1 for doc in docs if doc["kind"] == kind) for kind in KINDS}
    return {"docs": len(docs), **counts}


def list_documents(settings: Settings) -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    for row in fetch_orgaos(settings):
        if row.get("suspended"):
            continue
        docs.append(_doc("orgao", row["id"], row.get("razaoSocial")))
    for row in fetch_fornecedores(settings):
        if row.get("suspended"):
            continue
        docs.append(_doc("fornecedor", row["id"], row.get("razaoSocial")))
    for row in fetch_all_items(settings):
        if row.get("suspended"):
            continue
        docs.append(_doc("item", row["id"], row.get("descricao")))
    return docs


def _doc(kind: str, entity_id: object, text: object) -> dict[str, str]:
    eid = str(entity_id or "").strip()
    body = str(text or "").strip()
    if not eid:
        raise SystemExit(f"{kind} missing id")
    if not body:
        raise SystemExit(f"{kind} {eid} missing text")
    # Meili document ids allow only [A-Za-z0-9_-].
    return {"id": f"{kind}_{eid}", "kind": kind, "entityId": eid, "text": body}


def _assert_factual(docs: list[dict[str, str]]) -> None:
    for doc in docs:
        extra = set(doc) - set(DISPLAYED)
        if extra:
            raise SystemExit(f"search doc extra fields {sorted(extra)}")
        for key in doc:
            folded = key.casefold()
            if any(token in folded for token in BANNED_KEYS):
                raise SystemExit(f"search doc banned key {key}")


def _client(settings: Settings) -> httpx.Client:
    headers = {"content-type": "application/json"}
    if settings.meili_master_key:
        headers["authorization"] = f"Bearer {settings.meili_master_key}"
    return httpx.Client(base_url=settings.meili_url.rstrip("/"), headers=headers, timeout=20)


def _ensure_index(client: httpx.Client) -> None:
    try:
        _get_json(client, f"/indexes/{INDEX}")
        return
    except SearchUnavailable as exc:
        if exc.status != 404:
            raise
    _wait_task(client, _post_json(client, "/indexes", {"uid": INDEX, "primaryKey": PRIMARY_KEY}))


def _document_ids(client: httpx.Client) -> set[str]:
    ids: set[str] = set()
    offset = 0
    while True:
        page = _get_json(client, f"/indexes/{INDEX}/documents", params={"limit": CHUNK, "offset": offset, "fields": "id"})
        rows = page.get("results") or []
        ids.update(str(row.get("id") or "") for row in rows if row.get("id"))
        if len(rows) < CHUNK:
            return ids
        offset += CHUNK


def _wait_task(client: httpx.Client, task: dict[str, Any]) -> None:
    uid = task.get("taskUid", task.get("uid"))
    if uid is None:
        raise SystemExit(f"meili task missing uid: {task}")
    deadline = time.monotonic() + TASK_WAIT_S
    while time.monotonic() < deadline:
        got = _get_json(client, f"/tasks/{uid}")
        status = str(got.get("status") or "")
        if status == "succeeded":
            return
        if status in {"failed", "canceled"}:
            raise SystemExit(f"meili task {uid} {status}: {got.get('error')}")
        time.sleep(0.2)
    raise SystemExit(f"meili task {uid} timed out")


def _get_json(client: httpx.Client, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        resp = client.get(path, params=params)
    except httpx.HTTPError as exc:
        raise SearchUnavailable(0, str(exc)) from exc
    if resp.status_code >= 400:
        raise SearchUnavailable(resp.status_code, resp.text)
    return resp.json()


def _post_json(client: httpx.Client, path: str, payload: Any) -> dict[str, Any]:
    return _write_json(client.post, path, payload)


def _put_json(client: httpx.Client, path: str, payload: Any) -> dict[str, Any]:
    return _write_json(client.put, path, payload)


def _patch_json(client: httpx.Client, path: str, payload: Any) -> dict[str, Any]:
    return _write_json(client.patch, path, payload)


def _write_json(method, path: str, payload: Any) -> dict[str, Any]:
    try:
        resp = method(path, json=payload)
    except httpx.HTTPError as exc:
        raise SearchUnavailable(0, str(exc)) from exc
    if resp.status_code >= 400:
        raise SearchUnavailable(resp.status_code, resp.text)
    data = resp.json()
    if not isinstance(data, dict):
        raise SystemExit(f"meili {path} returned non-object")
    return data


def _chunks(rows: list[dict[str, str]], size: int):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


class SearchUnavailable(RuntimeError):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SearchUnavailable as exc:
        raise SystemExit(f"meili unavailable ({exc.status}): {exc}") from exc
