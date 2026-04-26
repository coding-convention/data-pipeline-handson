# Test Spec: Data Pipeline Hands-on Beacon Logs

## Metadata

- Status: Approved planning artifact
- Finalized UTC: `2026-04-26T14:49:54Z`
- Source spec: `.omx/specs/deep-interview-data-pipeline-hands-on-beacon-logs.md`
- Final plan: `.omx/plans/plan-data-pipeline-hands-on-beacon-logs.md`
- PRD: `.omx/plans/prd-data-pipeline-hands-on-beacon-logs.md`

## Verification Philosophy

Every layer must prove the previous layer produced usable data. Prefer deterministic shell/script checks over manual visual inspection, while still allowing the README to show what learners should look at.

## Test Matrix

| ID | Area | Verification | Expected Result |
|---|---|---|---|
| T-1 | Compose syntax | `docker compose config` | exits 0 |
| T-2 | Image build | `docker compose build` | `web` and `pipeline` build successfully |
| T-3 | Service startup | `docker compose up -d minio createbuckets web` | services start with default ports |
| T-4 | Health endpoint | `curl http://localhost:8000/health` | returns JSON `{"status":"ok"}` |
| T-5 | SQLite seed count | pipeline/container Python or sqlite query | `select count(*) from questions` returns `3` |
| T-6 | Quiz page | `curl http://localhost:8000/` or browser | page renders quiz content from SQLite |
| T-7 | Sample events | `scripts/generate_sample_events.py` | creates page_view, correct answer, incorrect answer, and skipped events |
| T-8 | Local raw spool | inspect `data/raw_spool/beacon_events/dt=*/events.jsonl` | JSONL exists and has non-zero rows |
| T-9 | Event type coverage | JSONL/DuckDB verification query | `page_view`, `answer_submitted`, `question_skipped` present |
| T-10 | Event field coverage | verification query/script | common fields populated; `is_correct` populated for answer events |
| T-11 | MinIO upload | `python scripts/upload_logs_to_minio.py` | objects appear under `s3://raw/beacon-events/dt=YYYY-MM-DD/` |
| T-12 | DuckDB load | `python scripts/load_minio_to_duckdb.py` | `warehouse/quiz.duckdb` and `raw_beacon_events` created |
| T-13 | dbt run | `dbt --project-dir dbt_quiz --profiles-dir dbt_quiz run` | staging/mart models succeed |
| T-14 | dbt tests | `dbt --project-dir dbt_quiz --profiles-dir dbt_quiz test` | all tests pass |
| T-15 | Report render | `python scripts/render_report.py` | `reports/quiz_pipeline_report.html` exists and contains non-empty metrics |
| T-16 | Guided replay | `bash scripts/run_full_pipeline.sh` | upload/load/dbt/report/verify sequence succeeds |
| T-17 | Final verifier | `python scripts/verify_pipeline.py` | prints evidence summary and exits 0 |
| T-18 | README checkpoints | follow README commands from fresh clone | checkpoints match expected output |
| T-19 | Docs boundary | inspect `docs/` | analytics-engineering/event/A-B guidance exists outside main README path |

## Required dbt Tests

- `not_null` and `unique` for event ID in staging/fact model.
- `not_null` for server/client timestamps where applicable.
- `accepted_values` for event type: `page_view`, `answer_submitted`, `question_skipped`.
- `not_null` for `question_id` on answer and skipped events.
- Accepted boolean values for `is_correct` on answer events.

## Required Verification Script Assertions

`scripts/verify_pipeline.py` should fail fast if any of these are false:

1. SQLite database exists and has exactly 3 questions.
2. Local spool has at least one JSONL event row.
3. Required event types are present.
4. Required fields are populated.
5. Both `is_correct=true` and `is_correct=false` appear after deterministic sample events.
6. MinIO raw objects exist at the documented path.
7. DuckDB file exists and contains raw plus dbt-derived tables.
8. Static report exists and includes non-empty metric values.

## Manual QA Checklist

- Open `http://localhost:8000` and confirm the app is intentionally plain but usable.
- Submit a correct answer, an incorrect answer, and skip a question.
- Confirm MinIO console shows raw JSONL objects.
- Open `reports/quiz_pipeline_report.html` and confirm charts/tables reflect generated events.
- Read `README.md` and verify that analytics-engineering material is linked to `docs/` rather than taught as the main path.

## Completion Evidence to Capture

Final implementation report should include command output for:

```bash
docker compose config
docker compose build
docker compose up -d minio createbuckets web
curl http://localhost:8000/health
docker compose run --rm pipeline bash scripts/run_full_pipeline.sh
docker compose run --rm pipeline python scripts/verify_pipeline.py
```

Also include a short list of generated artifacts: raw spool path, MinIO object prefix, DuckDB file, dbt models, and HTML report path.
