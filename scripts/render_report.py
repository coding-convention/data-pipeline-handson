from __future__ import annotations

import os
from pathlib import Path

import duckdb

DUCKDB_PATH = Path(os.environ.get("DUCKDB_PATH", "warehouse/quiz.duckdb"))
REPORT_PATH = Path(os.environ.get("REPORT_PATH", "reports/quiz_pipeline_report.html"))


def query_rows(query: str):
    with duckdb.connect(str(DUCKDB_PATH), read_only=True) as conn:
        return conn.execute(query).fetchall()


def main() -> int:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    event_counts = query_rows(
        "SELECT event_type, cnt FROM mart_quiz_summary_event_counts ORDER BY event_type"
    )
    answer_outcomes = query_rows(
        "SELECT answer_outcome, submissions FROM mart_quiz_summary_answer_outcomes ORDER BY answer_outcome"
    )
    skip_counts = query_rows(
        "SELECT question_id, skip_count FROM mart_quiz_summary_skip_counts ORDER BY question_id"
    )

    html = f"""<!doctype html>
<html lang=\"ko\">
  <head>
    <meta charset=\"utf-8\" />
    <title>Quiz Pipeline Report</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 2rem auto; max-width: 960px; }}
      table {{ border-collapse: collapse; width: 100%; margin-bottom: 2rem; }}
      th, td {{ border: 1px solid #d0d7de; padding: 0.6rem; text-align: left; }}
      th {{ background: #f6f8fa; }}
      .metric-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(3, 1fr); margin-bottom: 2rem; }}
      .metric {{ border: 1px solid #d0d7de; border-radius: 10px; padding: 1rem; }}
      .value {{ font-size: 1.8rem; font-weight: 700; }}
    </style>
  </head>
  <body>
    <h1>Beacon Log Pipeline Report</h1>
    <p>dbt 모델 결과를 기반으로 생성한 정적 리포트입니다.</p>
    <section class=\"metric-grid\">
      <div class=\"metric\"><div>이벤트 유형 수</div><div class=\"value\">{len(event_counts)}</div></div>
      <div class=\"metric\"><div>정답/오답 행 수</div><div class=\"value\">{sum(row[1] for row in answer_outcomes)}</div></div>
      <div class=\"metric\"><div>건너뛰기 질문 수</div><div class=\"value\">{sum(row[1] for row in skip_counts)}</div></div>
    </section>
    <h2>이벤트별 건수</h2>
    <table>
      <tr><th>event_type</th><th>count</th></tr>
      {''.join(f'<tr><td>{event_type}</td><td>{count}</td></tr>' for event_type, count in event_counts)}
    </table>
    <h2>정답/오답 제출 건수</h2>
    <table>
      <tr><th>answer_outcome</th><th>submissions</th></tr>
      {''.join(f'<tr><td>{outcome}</td><td>{count}</td></tr>' for outcome, count in answer_outcomes)}
    </table>
    <h2>문항별 skip 건수</h2>
    <table>
      <tr><th>question_id</th><th>skip_count</th></tr>
      {''.join(f'<tr><td>{question_id}</td><td>{count}</td></tr>' for question_id, count in skip_counts)}
    </table>
  </body>
</html>
"""
    REPORT_PATH.write_text(html, encoding="utf-8")
    print(f"Rendered report to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
