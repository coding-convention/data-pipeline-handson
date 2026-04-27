#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import boto3
import duckdb
from botocore.client import Config


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


DUCKDB_PATH = Path(env("DUCKDB_PATH", "warehouse/quiz.duckdb"))
MINIO_ENDPOINT = env("MINIO_ENDPOINT", env("AWS_ENDPOINT_URL", "http://localhost:9000"))
MINIO_ACCESS_KEY = env("MINIO_ACCESS_KEY", env("AWS_ACCESS_KEY_ID", env("MINIO_ROOT_USER", "minioadmin")))
MINIO_SECRET_KEY = env("MINIO_SECRET_KEY", env("AWS_SECRET_ACCESS_KEY", env("MINIO_ROOT_PASSWORD", "minioadmin")))
MINIO_BUCKET_RAW = env("MINIO_BUCKET_RAW", env("MINIO_BUCKET", "raw"))
OBJECT_PREFIX = env("RAW_OBJECT_PREFIX", "beacon-events")

SCHEMA_SQL = """
CREATE TABLE raw_beacon_events (
  event_id VARCHAR,
  event_type VARCHAR,
  schema_version VARCHAR,
  session_id VARCHAR,
  anonymous_user_id VARCHAR,
  occurred_at_client TIMESTAMP,
  received_at_server TIMESTAMP,
  page_url VARCHAR,
  user_agent VARCHAR,
  question_id BIGINT,
  selected_choice VARCHAR,
  correct_choice VARCHAR,
  is_correct BOOLEAN,
  skip_reason VARCHAR,
  referrer VARCHAR,
  quiz_step VARCHAR,
  display_order BIGINT,
  source_object_key VARCHAR,
  loaded_at TIMESTAMP DEFAULT current_timestamp,
  raw_payload JSON
)
"""


def minio_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=env("AWS_DEFAULT_REGION", "us-east-1"),
    )


def normalize_timestamp(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).replace("Z", "+00:00")


def list_event_rows() -> list[tuple[object, ...]]:
    client = minio_client()
    paginator = client.get_paginator("list_objects_v2")
    rows: list[tuple[object, ...]] = []
    prefix = OBJECT_PREFIX.rstrip("/") + "/"

    for page in paginator.paginate(Bucket=MINIO_BUCKET_RAW, Prefix=prefix):
        for item in page.get("Contents", []) or []:
            key = item["Key"]
            response = client.get_object(Bucket=MINIO_BUCKET_RAW, Key=key)
            body = response["Body"].read().decode("utf-8")
            for raw_line in body.splitlines():
                if not raw_line.strip():
                    continue
                payload = json.loads(raw_line)
                rows.append(
                    (
                        payload.get("event_id"),
                        payload.get("event_type"),
                        payload.get("schema_version"),
                        payload.get("session_id"),
                        payload.get("anonymous_user_id"),
                        normalize_timestamp(payload.get("occurred_at_client")),
                        normalize_timestamp(payload.get("received_at_server")),
                        payload.get("page_url"),
                        payload.get("user_agent"),
                        payload.get("question_id"),
                        payload.get("selected_choice"),
                        payload.get("correct_choice"),
                        payload.get("is_correct"),
                        payload.get("skip_reason"),
                        payload.get("referrer"),
                        payload.get("quiz_step"),
                        payload.get("display_order"),
                        key,
                        normalize_timestamp(payload.get("received_at_server")),
                        json.dumps(payload, ensure_ascii=False),
                    )
                )
    return rows


def main() -> int:
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = list_event_rows()
    if not rows:
        raise SystemExit(f"No raw events found in MinIO under {MINIO_BUCKET_RAW}/{OBJECT_PREFIX}/")

    with duckdb.connect(str(DUCKDB_PATH)) as conn:
        conn.execute("DROP TABLE IF EXISTS raw_beacon_events")
        conn.execute(SCHEMA_SQL)
        conn.executemany(
            """
            INSERT INTO raw_beacon_events (
              event_id, event_type, schema_version, session_id, anonymous_user_id,
              occurred_at_client, received_at_server, page_url, user_agent,
              question_id, selected_choice, correct_choice, is_correct, skip_reason,
              referrer, quiz_step, display_order, source_object_key, loaded_at, raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        total = conn.execute("SELECT COUNT(*) FROM raw_beacon_events").fetchone()[0]

    print(f"Loaded {total} raw events into {DUCKDB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
