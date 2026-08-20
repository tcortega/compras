from __future__ import annotations

import io
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import polars as pl

from compras_ingest.ids import sha256_bytes
from compras_ingest.settings import Settings


@dataclass(frozen=True)
class LandingRef:
    source: str
    partition_date: str
    sha256: str
    uri: str
    rows: int
    key: str

    def as_dict(self) -> dict:
        return asdict(self)


class LandingStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._kind, self._root = _parse_uri(settings.landing_uri)
        self._s3 = None
        if self._kind == "s3":
            self._s3 = _s3_client(settings)

    def write_parquet(self, source: str, partition_date: str, df: pl.DataFrame) -> LandingRef:
        buf = io.BytesIO()
        df.write_parquet(buf, compression="zstd")
        payload = buf.getvalue()
        digest = sha256_bytes(payload)
        key = f"{source}/date={partition_date}/{digest}.parquet"
        uri = self.put(key, payload)
        manifest = {
            "source": source,
            "partition_date": partition_date,
            "sha256": digest,
            "rows": df.height,
            "columns": df.columns,
            "written_at": datetime.now(timezone.utc).isoformat(),
        }
        self.put(f"{source}/date={partition_date}/{digest}.manifest.json", json.dumps(manifest).encode())
        return LandingRef(source, partition_date, digest, uri, df.height, key)

    def put(self, key: str, data: bytes) -> str:
        if self._kind == "file":
            path = self._root / key
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(data)
            return path.resolve().as_uri()
        assert self._s3 is not None
        bucket = self._root
        self._s3.put_object(Bucket=bucket, Key=key, Body=data)
        return f"s3://{bucket}/{key}"

    def exists(self, key: str) -> bool:
        if self._kind == "file":
            return (self._root / key).exists()
        assert self._s3 is not None
        try:
            self._s3.head_object(Bucket=self._root, Key=key)
            return True
        except Exception:
            return False

    def get(self, key: str) -> bytes:
        if self._kind == "file":
            return (self._root / key).read_bytes()
        assert self._s3 is not None
        resp = self._s3.get_object(Bucket=self._root, Key=key)
        return resp["Body"].read()

    def list_parquet(self, source: str) -> list[str]:
        prefix = f"{source}/"
        if self._kind == "file":
            root = self._root / source
            if not root.exists():
                return []
            return [str(p.relative_to(self._root)) for p in root.rglob("*.parquet")]
        assert self._s3 is not None
        keys: list[str] = []
        token = None
        while True:
            kw = {"Bucket": self._root, "Prefix": prefix}
            if token:
                kw["ContinuationToken"] = token
            resp = self._s3.list_objects_v2(**kw)
            for obj in resp.get("Contents") or []:
                if obj["Key"].endswith(".parquet"):
                    keys.append(obj["Key"])
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return keys

    def read_parquet(self, key: str) -> pl.DataFrame:
        return pl.read_parquet(io.BytesIO(self.get(key)))


def partition_date_of(values: list[date | datetime | None], fallback: date | None = None) -> str:
    dates = []
    for v in values:
        if v is None:
            continue
        dates.append(v.date() if isinstance(v, datetime) else v)
    if dates:
        return max(dates).isoformat()
    return (fallback or datetime.now(timezone.utc).date()).isoformat()


def _parse_uri(uri: str) -> tuple[str, Path | str]:
    if uri.startswith("s3://"):
        parsed = urlparse(uri)
        return "s3", parsed.netloc
    if uri.startswith("file://"):
        return "file", Path(urlparse(uri).path)
    return "file", Path(uri)


def _s3_client(settings: Settings):
    import boto3

    kw = {
        "aws_access_key_id": settings.s3_access_key or None,
        "aws_secret_access_key": settings.s3_secret_key or None,
        "region_name": settings.s3_region,
    }
    if settings.s3_endpoint:
        kw["endpoint_url"] = settings.s3_endpoint
    return boto3.client("s3", **kw)
