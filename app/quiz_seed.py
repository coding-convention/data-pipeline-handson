from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_QUESTIONS = [
    {
        "prompt": "DuckDB는 주로 어떤 용도로 많이 사용되나요?",
        "choice_a": "브라우저 렌더링 엔진",
        "choice_b": "임베디드 분석용 OLAP 데이터베이스",
        "choice_c": "모바일 운영체제",
        "correct_choice": "B",
    },
    {
        "prompt": "MinIO는 이 실습에서 어떤 역할을 하나요?",
        "choice_a": "원시 로그를 보관하는 오브젝트 스토리지",
        "choice_b": "프론트엔드 번들러",
        "choice_c": "DBT 테스트 러너",
        "correct_choice": "A",
    },
    {
        "prompt": "dbt 모델의 주요 목적은 무엇인가요?",
        "choice_a": "컨테이너 이미지를 빌드하기 위해",
        "choice_b": "원시 데이터를 읽기 쉬운 테이블로 변환하기 위해",
        "choice_c": "SQLite 인덱스를 삭제하기 위해",
        "correct_choice": "B",
    },
]


def init_db(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                choice_a TEXT NOT NULL,
                choice_b TEXT NOT NULL,
                choice_c TEXT NOT NULL,
                correct_choice TEXT NOT NULL
            )
            """
        )
        current_count = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if current_count != len(DEFAULT_QUESTIONS):
            connection.execute("DELETE FROM questions")
            connection.executemany(
                """
                INSERT INTO questions (prompt, choice_a, choice_b, choice_c, correct_choice)
                VALUES (:prompt, :choice_a, :choice_b, :choice_c, :correct_choice)
                """,
                DEFAULT_QUESTIONS,
            )
        connection.commit()
    finally:
        connection.close()
