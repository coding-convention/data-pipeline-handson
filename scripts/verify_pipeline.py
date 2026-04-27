#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_EVENT_TYPES = {"page_view", "answer_submitted", "question_skipped"}
REQUIRED_COMMON_FIELDS = {
    "event_id",
    "event_type",
    "schema_version",
    "session_id",
    "anonymous_user_id",
    "occurred_at_client",
    "received_at_server",
    "page_url",
    "user_agent",
}
REQUIRED_ANSWER_FIELDS = {"question_id", "selected_choice", "correct_choice", "is_correct"}
REQUIRED_SKIP_FIELDS = {"question_id", "skip_reason"}
REQUIRED_DBT_TABLES = {
    "stg_beacon_events",
    "fct_quiz_events",
    "mart_quiz_summary",
    "mart_access_log_funnel",
}
REQUIRED_RAW_COLUMNS = {"quiz_step", "display_order"}
REQUIRED_FUNNEL_COLUMNS = {
    "quiz_step",
    "display_order",
    "view_count",
    "answer_count",
    "skip_count",
    "session_count",
}
VALID_QUIZ_STEPS = {"landing", "question", "finish"}


@dataclass
class Evidence:
    label: str
    detail: str


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the beacon-log hands-on pipeline artifacts.")
    parser.add_argument("--bucket", default=os.getenv("RAW_BUCKET", "raw"))
    parser.add_argument("--prefix", default=os.getenv("RAW_PREFIX", "beacon-events/"))
    return parser.parse_args()


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_jsonl_events(spool_root: Path) -> tuple[list[dict[str, Any]], list[Path]]:
    files = sorted(spool_root.glob("beacon_events/dt=*/events.jsonl"))
    events: list[dict[str, Any]] = []
    for file_path in files:
        with file_path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    events.append(json.loads(stripped))
                except json.JSONDecodeError as exc:
                    raise AssertionError(f"Invalid JSON in {file_path}:{line_no}: {exc}") from exc
    return events, files


def assert_sqlite(root: Path) -> Evidence:
    sqlite_path = root / "app" / "data" / "quiz.sqlite3"
    ensure(sqlite_path.exists(), f"SQLite database missing: {sqlite_path}")
    with sqlite3.connect(sqlite_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    ensure(count == 3, f"Expected exactly 3 quiz questions, found {count}")
    return Evidence("SQLite seed", f"{sqlite_path} has exactly 3 questions")


def assert_question_scoped_event(index: int, event: dict[str, Any]) -> None:
    ensure(
        event.get("quiz_step") == "question",
        f"{event.get('event_type')} event #{index} must have quiz_step='question'",
    )
    ensure(
        event.get("display_order") is not None,
        f"{event.get('event_type')} event #{index} must have non-null display_order",
    )
    ensure(
        event.get("question_id") is not None,
        f"question-scoped event #{index} must have question_id",
    )


def assert_sample_sequence(events: list[dict[str, Any]]) -> Evidence:
    sample_events = [
        event
        for event in events
        if event.get("session_id") == "sample-session-001" and event.get("quiz_step") is not None
    ]
    sample_events.sort(key=lambda event: str(event.get("occurred_at_client", "")))
    expected = [
        ("page_view", "landing", None),
        ("page_view", "question", 1),
        ("answer_submitted", "question", 1),
        ("page_view", "question", 2),
        ("answer_submitted", "question", 2),
        ("page_view", "question", 3),
        ("question_skipped", "question", 3),
        ("page_view", "finish", None),
    ]
    actual = [
        (event.get("event_type"), event.get("quiz_step"), event.get("display_order"))
        for event in sample_events[: len(expected)]
    ]
    ensure(actual == expected, f"Deterministic sample sequence mismatch. expected={expected}, actual={actual}")

    answer_orders = [
        event.get("display_order")
        for event in sample_events
        if event.get("event_type") == "answer_submitted"
    ]
    skip_orders = [
        event.get("display_order")
        for event in sample_events
        if event.get("event_type") == "question_skipped"
    ]
    ensure(answer_orders[:2] == [1, 2], f"Sample answer display_order values must start [1, 2], got {answer_orders}")
    ensure(skip_orders[:1] == [3], f"Sample skip display_order values must start [3], got {skip_orders}")
    return Evidence("Sample access-log sequence", "landing → q1 answer → q2 answer → q3 skip → finish with display_order 1/2/3")


def assert_spool(root: Path) -> tuple[list[dict[str, Any]], list[Evidence], list[str]]:
    spool_root = root / "data" / "raw_spool"
    ensure(spool_root.exists(), f"Spool root missing: {spool_root}")
    events, files = read_jsonl_events(spool_root)
    ensure(files, "No spool JSONL files found under data/raw_spool/beacon_events/dt=*/events.jsonl")
    ensure(events, "Spool files exist but contain zero events")

    event_types = Counter(event.get("event_type") for event in events)
    missing_types = REQUIRED_EVENT_TYPES - set(event_types)
    ensure(not missing_types, f"Missing required event types: {sorted(missing_types)}")

    true_seen = False
    false_seen = False
    page_view_steps: set[str] = set()
    question_display_orders: set[int] = set()

    for index, event in enumerate(events, start=1):
        missing_common = [field for field in REQUIRED_COMMON_FIELDS if event.get(field) in (None, "")]
        ensure(not missing_common, f"Event #{index} missing common fields: {missing_common}")

        quiz_step = event.get("quiz_step")
        if quiz_step is not None:
            ensure(quiz_step in VALID_QUIZ_STEPS, f"Event #{index} has invalid quiz_step={quiz_step!r}")
        if event.get("event_type") == "page_view":
            ensure(quiz_step is not None, f"page_view event #{index} must have quiz_step")
            page_view_steps.add(str(quiz_step))
        if quiz_step == "question":
            if event.get("event_type") == "page_view":
                assert_question_scoped_event(index, event)
            if event.get("display_order") is not None:
                question_display_orders.add(int(event["display_order"]))
        if quiz_step in {"landing", "finish"}:
            ensure(
                event.get("event_type") == "page_view",
                f"{quiz_step} event #{index} must be page_view, got {event.get('event_type')}",
            )
            ensure(event.get("display_order") is None, f"{quiz_step} event #{index} must have null display_order")

        if event.get("event_type") == "answer_submitted":
            missing_answer = [field for field in REQUIRED_ANSWER_FIELDS if event.get(field) in (None, "")]
            ensure(not missing_answer, f"Answer event #{index} missing fields: {missing_answer}")
            assert_question_scoped_event(index, event)
            ensure(
                isinstance(event.get("is_correct"), bool),
                f"Answer event #{index} has non-boolean is_correct={event.get('is_correct')!r}",
            )
            true_seen = true_seen or event["is_correct"] is True
            false_seen = false_seen or event["is_correct"] is False

        if event.get("event_type") == "question_skipped":
            missing_skip = [field for field in REQUIRED_SKIP_FIELDS if event.get(field) in (None, "")]
            ensure(not missing_skip, f"Skipped event #{index} missing fields: {missing_skip}")
            assert_question_scoped_event(index, event)

    ensure(true_seen and false_seen, "Expected both correct and incorrect answer_submitted outcomes")
    ensure(
        {"landing", "question", "finish"}.issubset(page_view_steps),
        f"Expected page_view rows for landing/question/finish, got {sorted(page_view_steps)}",
    )
    ensure(
        {1, 2, 3}.issubset(question_display_orders),
        f"Expected question-scoped display_order values 1, 2, 3, got {sorted(question_display_orders)}",
    )

    evidence = [
        Evidence("Spool files", ", ".join(str(path.relative_to(root)) for path in files)),
        Evidence("Event counts", ", ".join(f"{k}={v}" for k, v in sorted(event_types.items()))),
        assert_sample_sequence(events),
    ]
    partitions = sorted({path.parent.name for path in files})
    return events, evidence, partitions


def build_s3_client() -> Any:
    try:
        import boto3  # type: ignore
    except ImportError as exc:
        raise AssertionError("boto3 is required to verify MinIO objects") from exc

    endpoint = (
        os.getenv("MINIO_ENDPOINT")
        or os.getenv("S3_ENDPOINT")
        or os.getenv("AWS_ENDPOINT_URL")
        or f"http://{os.getenv('MINIO_HOST', 'minio')}:{os.getenv('MINIO_API_PORT', '9000')}"
    )
    access_key = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("MINIO_ROOT_USER") or "minioadmin"
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("MINIO_ROOT_PASSWORD") or "minioadmin"

    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def assert_minio(bucket: str, prefix: str, partitions: list[str]) -> Evidence:
    client = build_s3_client()
    prefixes = [prefix.rstrip("/") + "/" + partition + "/" for partition in partitions] or [prefix]

    matched_keys: list[str] = []
    for candidate_prefix in prefixes:
        response = client.list_objects_v2(Bucket=bucket, Prefix=candidate_prefix)
        for item in response.get("Contents", []) or []:
            matched_keys.append(item["Key"])

    ensure(matched_keys, f"No MinIO objects found in s3://{bucket}/{prefix}")
    preview = ", ".join(matched_keys[:3])
    return Evidence("MinIO objects", f"s3://{bucket}/{prefix} -> {preview}")


def table_columns(conn: Any, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    return {row[1] for row in rows}


def assert_duckdb(root: Path) -> Evidence:
    duckdb_path = root / "warehouse" / "quiz.duckdb"
    ensure(duckdb_path.exists(), f"DuckDB file missing: {duckdb_path}")

    try:
        import duckdb  # type: ignore
    except ImportError as exc:
        raise AssertionError("duckdb package is required to verify warehouse tables") from exc

    conn = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
        ensure("raw_beacon_events" in tables, "raw_beacon_events table missing from DuckDB")
        missing_tables = REQUIRED_DBT_TABLES - tables
        ensure(not missing_tables, f"Missing dbt-derived tables: {sorted(missing_tables)}")

        raw_columns = table_columns(conn, "raw_beacon_events")
        ensure(
            REQUIRED_RAW_COLUMNS.issubset(raw_columns),
            f"raw_beacon_events missing access-log columns: {sorted(REQUIRED_RAW_COLUMNS - raw_columns)}",
        )
        funnel_columns = table_columns(conn, "mart_access_log_funnel")
        ensure(
            REQUIRED_FUNNEL_COLUMNS.issubset(funnel_columns),
            f"mart_access_log_funnel missing columns: {sorted(REQUIRED_FUNNEL_COLUMNS - funnel_columns)}",
        )
        raw_count = conn.execute("SELECT COUNT(*) FROM raw_beacon_events").fetchone()[0]
        ensure(raw_count > 0, "raw_beacon_events exists but has zero rows")
        funnel_view_rows = conn.execute(
            "SELECT COUNT(*) FROM mart_access_log_funnel WHERE view_count > 0"
        ).fetchone()[0]
        ensure(funnel_view_rows > 0, "mart_access_log_funnel has no rows with view_count > 0")
    finally:
        conn.close()

    return Evidence(
        "DuckDB tables",
        f"{duckdb_path} has raw access columns and dbt tables ({', '.join(sorted(REQUIRED_DBT_TABLES))})",
    )


def assert_report(root: Path) -> Evidence:
    report_path = root / "reports" / "quiz_pipeline_report.html"
    ensure(report_path.exists(), f"Report missing: {report_path}")
    content = report_path.read_text(encoding="utf-8")
    ensure(content.strip(), "Report file is empty")
    ensure("접속/문항 노출 퍼널" in content, "Report is missing section title: 접속/문항 노출 퍼널")
    digit_count = sum(character.isdigit() for character in content)
    ensure(digit_count > 0, "Report does not appear to contain metric values")
    return Evidence("Report", f"{report_path} exists and contains 접속/문항 노출 퍼널")


def main() -> int:
    args = parse_args()
    root = repo_root()
    evidence: list[Evidence] = []

    try:
        evidence.append(assert_sqlite(root))
        _, spool_evidence, partitions = assert_spool(root)
        evidence.extend(spool_evidence)
        evidence.append(assert_minio(args.bucket, args.prefix, partitions))
        evidence.append(assert_duckdb(root))
        evidence.append(assert_report(root))
    except AssertionError as exc:
        print(f"VERIFY FAIL: {exc}", file=sys.stderr)
        return 1

    print("Verification:")
    for item in evidence:
        print(f"PASS - {item.label}: {item.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
