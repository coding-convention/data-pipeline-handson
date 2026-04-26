# PRD: Data Pipeline Hands-on Beacon Logs

## Metadata

- Status: Approved planning artifact
- Finalized UTC: `2026-04-26T14:49:54Z`
- Source spec: `.omx/specs/deep-interview-data-pipeline-hands-on-beacon-logs.md`
- Final plan: `.omx/plans/plan-data-pipeline-hands-on-beacon-logs.md`
- Test spec: `.omx/plans/test-spec-data-pipeline-hands-on-beacon-logs.md`

## Problem / Opportunity

Beginners often see data engineering as a list of tools rather than an end-to-end path from product behavior to usable data. This lab should make the path visible: a browser action emits a log, the log lands as raw data, the raw data is loaded into an analytical store, dbt creates usable models, and a simple report confirms the result.

## Target Learner

- Early data-engineering learner or software developer exploring data pipelines.
- Comfortable copying shell/Python snippets and running Docker Compose.
- Not expected to design production analytics events or statistical A/B tests during the main lab.

## Goals

1. Teach the blueprint of logs becoming data.
2. Provide a deterministic Korean README that learners can follow by copy/paste.
3. Use a minimal quiz application to create realistic user interaction logs.
4. Demonstrate raw object storage in MinIO, local analytical storage in DuckDB, and transformations/tests in dbt.
5. End with a provided visualization that proves the pipeline worked.

## Non-goals

- Polished UI/UX.
- Production auth/user accounts/deployment.
- Full analytics-engineering curriculum in the main README.
- Student-built dashboard design.
- Deep A/B test statistics or metric governance in the main path.
- Streaming/distributed infrastructure.

## Product Scope

### Main README path

1. Start Docker Compose services.
2. Initialize SQLite with exactly 3 quiz questions.
3. Open the quiz app on `http://localhost:8000`.
4. Generate beacon events for page views, answer submissions, and skipped questions.
5. Inspect local JSONL raw spool files.
6. Upload raw logs to MinIO under `s3://raw/beacon-events/dt=YYYY-MM-DD/`.
7. Load MinIO raw data into `warehouse/quiz.duckdb`.
8. Run dbt models/tests against DuckDB.
9. Render `reports/quiz_pipeline_report.html`.
10. Run `scripts/run_full_pipeline.sh` only as a post-lesson replay wrapper.

### Supporting docs

- `docs/data-engineering-vs-analytics-engineering.md`
- `docs/event-design-and-ab-testing.md`
- `docs/pipeline-architecture.md`

## Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | Docker Compose defines `web`, `minio`, `createbuckets`, and `pipeline` services. |
| FR-2 | `.env.example` defines default `WEB_PORT=8000`, `MINIO_API_PORT=9000`, and `MINIO_CONSOLE_PORT=9001`. |
| FR-3 | Flask app provides `GET /health` returning `{"status":"ok"}`. |
| FR-4 | SQLite seed contains exactly 3 quiz questions. |
| FR-5 | Browser beacon client emits `page_view`, `answer_submitted`, and `question_skipped`. |
| FR-6 | Beacon endpoint writes newline-delimited JSON to `data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl`. |
| FR-7 | Events include the minimum common fields: `event_id`, `event_type`, `schema_version`, `session_id`, `anonymous_user_id`, `occurred_at_client`, `received_at_server`, `page_url`, `user_agent`. |
| FR-8 | `answer_submitted` includes `question_id`, `selected_choice`, `correct_choice`, and `is_correct`. |
| FR-9 | `question_skipped` includes `question_id` and `skip_reason`. |
| FR-10 | Upload script stores raw JSONL objects in MinIO with documented partition-like paths. |
| FR-11 | DuckDB load script creates `warehouse/quiz.duckdb` and `raw_beacon_events`. |
| FR-12 | dbt project creates staging and mart models from `raw_beacon_events`. |
| FR-13 | dbt tests validate IDs, timestamps, accepted event types, and required fields. |
| FR-14 | Static report renders non-empty values from dbt output. |
| FR-15 | README provides verification checkpoints after each major layer. |

## UX / Learning Requirements

- README language should be Korean.
- Each chapter should explain “what boundary did we just cross?” before the command/checkpoint.
- Copy/paste blocks should be deterministic from a fresh clone.
- Troubleshooting should cover Docker, MinIO credentials, missing events, dbt profile path, and reset commands.

## Acceptance Criteria

See `.omx/plans/test-spec-data-pipeline-hands-on-beacon-logs.md` for the executable verification matrix. At minimum, the implementation is accepted only when Docker Compose starts, exactly 3 questions are seeded, all required event types/fields are present, MinIO upload succeeds, DuckDB/dbt transformations pass, the HTML report is generated, and README/docs boundaries are complete.

## Milestones

1. Scaffold Compose, app, volumes, and health checks.
2. Implement quiz and beacon logging.
3. Implement MinIO/DuckDB/dbt pipeline.
4. Implement static report and replay wrapper.
5. Write README/docs.
6. Run complete verification and fix gaps.

## Open Decisions

None blocking. The plan authorizes implementation choices within the agreed scope; escalate only for major new dependencies or scope changes.
