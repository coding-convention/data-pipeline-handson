#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


RAW_SPOOL_DIR = Path(env("RAW_SPOOL_DIR", "data/raw_spool"))
MINIO_ENDPOINT = env("MINIO_ENDPOINT", env("AWS_ENDPOINT_URL", "http://localhost:9000"))
MINIO_ACCESS_KEY = env("MINIO_ACCESS_KEY", env("AWS_ACCESS_KEY_ID", env("MINIO_ROOT_USER", "minioadmin")))
MINIO_SECRET_KEY = env("MINIO_SECRET_KEY", env("AWS_SECRET_ACCESS_KEY", env("MINIO_ROOT_PASSWORD", "minioadmin")))
MINIO_BUCKET_RAW = env("MINIO_BUCKET_RAW", env("MINIO_BUCKET", "raw"))
OBJECT_PREFIX = env("RAW_OBJECT_PREFIX", "beacon-events")


def minio_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=env("AWS_DEFAULT_REGION", "us-east-1"),
    )


def object_key_for(file_path: Path) -> str:
    relative = file_path.relative_to(RAW_SPOOL_DIR).as_posix()
    # Local spool keeps the app-friendly folder name `beacon_events`; MinIO uses
    # the documented tutorial prefix `beacon-events/dt=YYYY-MM-DD/events.jsonl`.
    return relative.replace("beacon_events/", f"{OBJECT_PREFIX.rstrip('/')}/", 1)


def main() -> int:
    files = sorted(RAW_SPOOL_DIR.glob("beacon_events/dt=*/events.jsonl"))
    if not files:
        raise SystemExit(f"No spool files found under {RAW_SPOOL_DIR}")

    client = minio_client()
    try:
        client.create_bucket(Bucket=MINIO_BUCKET_RAW)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
            raise
    uploaded: list[str] = []
    for file_path in files:
        object_key = object_key_for(file_path)
        client.upload_file(str(file_path), MINIO_BUCKET_RAW, object_key)
        uploaded.append(f"s3://{MINIO_BUCKET_RAW}/{object_key}")

    print("Uploaded spool files:")
    for item in uploaded:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
