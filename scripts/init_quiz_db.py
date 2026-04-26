#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.quiz_seed import init_db  # noqa: E402


if __name__ == "__main__":
    db_path = ROOT_DIR / "app" / "data" / "quiz.sqlite3"
    init_db(db_path)
    print(f"Initialized {db_path.relative_to(ROOT_DIR)} with 3 quiz questions.")
