#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


COMMON_SCHEMA_VERSION = "1.0.0"
DEFAULT_PAGE_URL = "http://localhost:8000/"
DEFAULT_USER_AGENT = "sample-generator/1.0"


@dataclass(frozen=True)
class QuestionSeed:
    question_id: int
    correct_choice: str


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def utc_now() -> datetime:
    return datetime.now(UTC)


def isoformat_z(ts: datetime) -> str:
    return ts.isoformat(timespec="seconds").replace("+00:00", "Z")


def load_questions(sqlite_path: Path) -> list[QuestionSeed]:
    if not sqlite_path.exists():
        return [
            QuestionSeed(question_id=1, correct_choice="A"),
            QuestionSeed(question_id=2, correct_choice="B"),
            QuestionSeed(question_id=3, correct_choice="C"),
        ]

    with sqlite3.connect(sqlite_path) as conn:
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(questions)").fetchall()
        }
        if "id" not in columns:
            return [
                QuestionSeed(question_id=1, correct_choice="A"),
                QuestionSeed(question_id=2, correct_choice="B"),
                QuestionSeed(question_id=3, correct_choice="C"),
            ]

        correct_column = None
        for candidate in ("correct_choice", "correct_answer", "answer"):
            if candidate in columns:
                correct_column = candidate
                break

        if correct_column is None:
            rows = conn.execute(
                "SELECT id FROM questions ORDER BY id LIMIT 3"
            ).fetchall()
            return [
                QuestionSeed(question_id=int(row[0]), correct_choice=choice)
                for row, choice in zip(rows, ["A", "B", "C"], strict=False)
            ]

        rows = conn.execute(
            f"SELECT id, {correct_column} FROM questions ORDER BY id LIMIT 3"
        ).fetchall()
        seeds: list[QuestionSeed] = []
        for idx, row in enumerate(rows, start=1):
            default_choice = ["A", "B", "C"][idx - 1]
            correct_choice = str(row[1]) if row[1] is not None else default_choice
            seeds.append(QuestionSeed(question_id=int(row[0]), correct_choice=correct_choice))
        return seeds or [
            QuestionSeed(question_id=1, correct_choice="A"),
            QuestionSeed(question_id=2, correct_choice="B"),
            QuestionSeed(question_id=3, correct_choice="C"),
        ]


def wrong_choice(correct_choice: str) -> str:
    options = ["A", "B", "C", "D"]
    return next((choice for choice in options if choice != correct_choice), "Z")


def build_event(event_type: str, seed: str, occurred_at: datetime, **payload: Any) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid5(uuid.NAMESPACE_URL, seed)),
        "event_type": event_type,
        "schema_version": COMMON_SCHEMA_VERSION,
        "session_id": "sample-session-001",
        "anonymous_user_id": "sample-user-001",
        "occurred_at_client": isoformat_z(occurred_at),
        "received_at_server": isoformat_z(occurred_at),
        "page_url": DEFAULT_PAGE_URL,
        "user_agent": DEFAULT_USER_AGENT,
        **payload,
    }


def write_events(output_path: Path, events: list[dict[str, Any]], overwrite: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if overwrite else "a"
    with output_path.open(mode, encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic beacon sample events in the local raw spool."
    )
    parser.add_argument(
        "--date",
        default=utc_now().date().isoformat(),
        help="Partition date in YYYY-MM-DD format (default: today in UTC).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the target JSONL file instead of appending.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not str(args.date).strip():
        raise SystemExit("--date must be a non-empty YYYY-MM-DD value")
    root = repo_root()
    sqlite_path = root / "app" / "data" / "quiz.sqlite3"
    questions = load_questions(sqlite_path)
    while len(questions) < 3:
        questions.append(
            QuestionSeed(
                question_id=len(questions) + 1,
                correct_choice=["A", "B", "C"][len(questions)],
            )
        )

    partition_path = (
        root / "data" / "raw_spool" / "beacon_events" / f"dt={args.date}" / "events.jsonl"
    )
    base_time = utc_now().replace(microsecond=0)
    q1, q2, q3 = questions[:3]

    events = [
        build_event(
            "page_view",
            f"page_view:landing:{args.date}",
            base_time,
            question_id=None,
            quiz_step="landing",
            display_order=None,
            referrer="direct",
        ),
        build_event(
            "page_view",
            f"page_view:question:1:{args.date}",
            base_time + timedelta(seconds=1),
            question_id=q1.question_id,
            quiz_step="question",
            display_order=1,
            referrer=None,
        ),
        build_event(
            "answer_submitted",
            f"answer_submitted:correct:{args.date}",
            base_time + timedelta(seconds=2),
            question_id=q1.question_id,
            quiz_step="question",
            display_order=1,
            selected_choice=q1.correct_choice,
            correct_choice=q1.correct_choice,
            is_correct=True,
        ),
        build_event(
            "page_view",
            f"page_view:question:2:{args.date}",
            base_time + timedelta(seconds=3),
            question_id=q2.question_id,
            quiz_step="question",
            display_order=2,
            referrer=None,
        ),
        build_event(
            "answer_submitted",
            f"answer_submitted:incorrect:{args.date}",
            base_time + timedelta(seconds=4),
            question_id=q2.question_id,
            quiz_step="question",
            display_order=2,
            selected_choice=wrong_choice(q2.correct_choice),
            correct_choice=q2.correct_choice,
            is_correct=False,
        ),
        build_event(
            "page_view",
            f"page_view:question:3:{args.date}",
            base_time + timedelta(seconds=5),
            question_id=q3.question_id,
            quiz_step="question",
            display_order=3,
            referrer=None,
        ),
        build_event(
            "question_skipped",
            f"question_skipped:{args.date}",
            base_time + timedelta(seconds=6),
            question_id=q3.question_id,
            quiz_step="question",
            display_order=3,
            skip_reason="next_question",
        ),
        build_event(
            "page_view",
            f"page_view:finish:{args.date}",
            base_time + timedelta(seconds=7),
            question_id=None,
            quiz_step="finish",
            display_order=None,
            referrer=None,
        ),
    ]

    write_events(partition_path, events, overwrite=args.overwrite)
    print(f"Wrote {len(events)} sample events to {partition_path}")
    print("Event sequence:")
    for event in events:
        print(
            "- {event_type} quiz_step={quiz_step} question_id={question_id} display_order={display_order}".format(
                **event
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
