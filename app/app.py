from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from quiz_seed import init_db

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("APP_SQLITE_PATH", BASE_DIR / "data" / "quiz.sqlite3"))
RAW_SPOOL_DIR = Path(os.getenv("APP_RAW_SPOOL_DIR", BASE_DIR / "data" / "raw_spool"))
SUPPORTED_EVENT_TYPES = {"page_view", "answer_submitted", "question_skipped"}
REQUIRED_FIELDS = {
    "event_id",
    "event_type",
    "schema_version",
    "session_id",
    "anonymous_user_id",
    "occurred_at_client",
    "page_url",
    "user_agent",
}

app = Flask(__name__)
init_db(DATABASE_PATH)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def load_questions() -> list[dict[str, Any]]:
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT id, prompt, choice_a, choice_b, choice_c, correct_choice FROM questions ORDER BY id"
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def parse_request_json() -> dict[str, Any]:
    if request.is_json:
        payload = request.get_json(silent=True)
        if isinstance(payload, dict):
            return payload
    raw_body = request.get_data(cache=False, as_text=True)
    if raw_body:
        parsed = json.loads(raw_body)
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("Request body must be a JSON object")


def validate_event(payload: dict[str, Any]) -> list[str]:
    missing = sorted(field for field in REQUIRED_FIELDS if not payload.get(field))
    if missing:
        return [f"missing required fields: {', '.join(missing)}"]
    if payload["event_type"] not in SUPPORTED_EVENT_TYPES:
        return [f"unsupported event_type: {payload['event_type']}"]
    if payload["event_type"] == "answer_submitted" and payload.get("is_correct") is None:
        return ["answer_submitted events require is_correct"]
    if payload["event_type"] in {"answer_submitted", "question_skipped"} and not payload.get("question_id"):
        return [f"{payload['event_type']} events require question_id"]
    return []


def spool_event(payload: dict[str, Any]) -> Path:
    received_at_server = utc_now_iso()
    partition_dir = RAW_SPOOL_DIR / "beacon_events" / f"dt={received_at_server[:10]}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    event_path = partition_dir / "events.jsonl"
    record = {
        **payload,
        "received_at_server": received_at_server,
        "server_metadata": {
            "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
            "request_id": request.headers.get("X-Request-Id", str(uuid.uuid4())),
        },
    }
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return event_path


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok"})


@app.get("/")
def index() -> str:
    return render_template("index.html", questions=load_questions())


@app.get("/api/questions")
def questions() -> Any:
    return jsonify({"questions": load_questions()})


@app.post("/api/answer")
def answer_question() -> Any:
    payload = parse_request_json()
    question_id = int(payload.get("question_id", 0))
    selected_choice = str(payload.get("selected_choice", "")).upper()
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT id, correct_choice FROM questions WHERE id = ?",
            (question_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return jsonify({"error": "question not found"}), 404
    return jsonify(
        {
            "question_id": question_id,
            "selected_choice": selected_choice,
            "correct_choice": row["correct_choice"],
            "is_correct": selected_choice == row["correct_choice"],
        }
    )


@app.post("/api/skip")
def skip_question() -> Any:
    payload = parse_request_json()
    return jsonify(
        {
            "question_id": payload.get("question_id"),
            "skip_reason": payload.get("skip_reason", "next_question"),
            "status": "recorded",
        }
    )


@app.post("/beacon")
def beacon() -> Any:
    try:
        payload = parse_request_json()
    except (ValueError, json.JSONDecodeError) as exc:
        return jsonify({"error": str(exc)}), 400
    errors = validate_event(payload)
    if errors:
        return jsonify({"errors": errors}), 400
    event_path = spool_event(payload)
    return jsonify({"status": "accepted", "path": str(event_path.relative_to(RAW_SPOOL_DIR))}), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
