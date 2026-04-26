# Final Consensus Plan: Data Pipeline Hands-on Beacon Logs

## Consensus Status

- Status: **APPROVED** by Architect and Critic short-mode consensus.
- Finalized UTC: `2026-04-26T14:49:54Z`
- Source spec: `.omx/specs/deep-interview-data-pipeline-hands-on-beacon-logs.md`
- PRD: `.omx/plans/prd-data-pipeline-hands-on-beacon-logs.md`
- Test spec: `.omx/plans/test-spec-data-pipeline-hands-on-beacon-logs.md`

## Requirements Summary

Build a greenfield, README-first Korean data-engineering hands-on lab. A learner starts from this repository, runs services with Docker Compose, uses a simple SQLite-backed quiz app, emits web beacon logs, stores raw logs in MinIO, loads/transforms them with DuckDB and dbt, and opens a provided static visualization to verify the pipeline. This follows the desired end-to-end outcome in spec lines 32-41, the README/local lab scope in lines 47-56, required events in lines 60-68, stack constraints in lines 106-113, and acceptance criteria in lines 119-130.

The main README must stay focused on data engineering. Analytics-engineering topics such as event design, metrics, and A/B testing should be placed in `docs/` reading material, consistent with spec lines 70-87 and assumptions in lines 132-141.

## Source Requirements

- Deep interview spec: `.omx/specs/deep-interview-data-pipeline-hands-on-beacon-logs.md`
- Key cited lines:
  - End-to-end desired outcome: spec lines 32-41.
  - README and local setup scope: spec lines 47-56.
  - Required beacon events: spec lines 60-68.
  - `docs/` analytics-engineering boundary: spec lines 70-77 and 79-87.
  - Autonomy for implementation choices: spec lines 89-104.
  - Required stack and greenfield scaffold: spec lines 106-113.
  - Acceptance criteria: spec lines 119-130.

## RALPLAN-DR Summary

### Principles

1. **Teach the blueprint, not tool trivia** — every step should map to log generation, raw storage, loading, modeling, or verification.
2. **Copy/paste deterministic path** — README commands should be executable from a fresh clone with minimal branching.
3. **Separate DE from analytics-engineering scope** — event/metric/A-B analysis theory belongs in `docs/`, not the core hands-on path.
4. **Prefer small, inspectable components** — use scripts and files learners can open over opaque orchestration.
5. **Verify after every layer** — app, raw logs, MinIO, DuckDB, dbt, and visualization each need a checkpoint.

### Decision Drivers

1. **Learner comprehension**: beginners should see where data is created, moved, stored, modeled, and viewed.
2. **Operational simplicity**: Docker Compose should start services; learner commands should be predictable.
3. **Stack alignment**: must include SQLite, MinIO, DuckDB, and dbt as first-class parts of the lab.

### Viable Options

#### Option A — Flask quiz app + file spool + explicit batch upload/load scripts (favored)

- **Approach**: Browser sends beacon events to a Flask `/beacon` endpoint. Flask writes JSONL to a local raw spool. Learners run pipeline scripts to upload JSONL to MinIO, load/query it in DuckDB, run dbt models, then render a static HTML report.
- **Pros**:
  - Makes each DE boundary visible: app log emission, raw file, object storage, warehouse file, model, report.
  - Keeps MinIO/DuckDB/dbt interactions in learner-run scripts that README can explain and verify.
  - Avoids request-path coupling between the quiz app and object storage.
- **Cons**:
  - Less “real time” than direct upload.
  - Requires learners to run several pipeline commands manually.

#### Option B — Flask/FastAPI app writes directly to MinIO on each beacon request

- **Approach**: `/beacon` receives events and uploads immediately to MinIO.
- **Pros**:
  - Fewer scripts; raw logs appear in MinIO quickly.
  - Simple final demo path.
- **Cons**:
  - Hides the ingestion boundary and makes app availability depend on object storage.
  - Harder to teach raw local logs vs object storage vs loading as separate stages.

#### Option C — Add a collector service that receives beacons and streams/buffers to MinIO

- **Approach**: Quiz app sends beacons to a separate collector container; collector stores raw logs in MinIO.
- **Pros**:
  - Clean production-like separation between app and collection service.
  - Teaches collector as independent data platform component.
- **Cons**:
  - More moving parts for a beginner lab.
  - Risks shifting focus from blueprint to microservice plumbing.

### Favored Option

Choose **Option A**. It is the strongest fit for a README-first beginner lab because every boundary is visible, inspectable, and testable. Mention Options B/C briefly in `docs/` as future production variants.

## Proposed Architecture

```text
Browser quiz page
  └─ navigator.sendBeacon/fetch
      └─ Flask app /beacon
          ├─ SQLite quiz DB: app/data/quiz.sqlite3
          └─ JSONL spool: data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl

Shared Compose bind mounts
  ├─ ./data/raw_spool  -> web:/app/data/raw_spool and pipeline:/workspace/data/raw_spool
  ├─ ./warehouse       -> pipeline:/workspace/warehouse
  ├─ ./reports         -> pipeline:/workspace/reports
  └─ ./app/data        -> web:/app/data and pipeline:/workspace/app/data

Learner commands
  ├─ scripts/upload_logs_to_minio.py
  │   └─ MinIO bucket/path: s3://raw/beacon-events/dt=YYYY-MM-DD/events-*.jsonl
  ├─ scripts/load_minio_to_duckdb.py
  │   └─ DuckDB file: warehouse/quiz.duckdb table raw_beacon_events
  ├─ dbt run/test
  │   └─ dbt models: stg_beacon_events, fct_quiz_events, mart_quiz_summary
  └─ scripts/render_report.py
      └─ reports/quiz_pipeline_report.html

Guided replay
  └─ scripts/run_full_pipeline.sh runs upload -> load -> dbt run/test -> render -> verify after learners have seen each manual boundary; it is a post-lesson convenience wrapper, not the primary learning path.
```

### Minimum Event Contract

All events should include: `event_id`, `event_type`, `schema_version`, `session_id`, `anonymous_user_id`, `occurred_at_client`, `received_at_server`, `page_url`, and `user_agent`.

Event-specific fields:

- `page_view`: optional `question_id`, `referrer`.
- `answer_submitted`: `question_id`, `selected_choice`, `correct_choice`, `is_correct`.
- `question_skipped`: `question_id`, `skip_reason` such as `next_question`.

The implementation may add fields, but dbt tests and the report should rely only on this minimum contract.

## Planned File Structure

```text
README.md
docker-compose.yml
.env.example
app/
  Dockerfile
  requirements.txt
  app.py
  templates/index.html
  static/beacon.js
  data/.gitkeep
scripts/
  init_quiz_db.py
  generate_sample_events.py
  upload_logs_to_minio.py
  load_minio_to_duckdb.py
  render_report.py
  verify_pipeline.py
  run_full_pipeline.sh
pipeline/
  Dockerfile
  requirements.txt
dbt_quiz/
  dbt_project.yml
  profiles.yml.example
  models/sources.yml
  models/staging/stg_beacon_events.sql
  models/marts/fct_quiz_events.sql
  models/marts/mart_quiz_summary.sql
  models/schema.yml
docs/
  data-engineering-vs-analytics-engineering.md
  event-design-and-ab-testing.md
  pipeline-architecture.md
data/
  raw_spool/.gitkeep
warehouse/.gitkeep
reports/.gitkeep
```

## Implementation Steps

1. **Create base project skeleton and Compose services**
   - Add `docker-compose.yml` with `web`, `minio`, `createbuckets`, and `pipeline` services plus explicit bind mounts for `./data/raw_spool`, `./app/data`, `./warehouse`, and `./reports`.
   - Add `.env.example` with stable local credentials and ports, including `WEB_PORT=8000`, `MINIO_API_PORT=9000`, and `MINIO_CONSOLE_PORT=9001`.
   - Add `app/Dockerfile` and `pipeline/Dockerfile`.
   - Ensure `docker compose up -d minio createbuckets web` starts the local lab.

2. **Build the simple SQLite-backed quiz app**
   - Implement Flask app in `app/app.py`, including `GET /health` returning JSON `{"status":"ok"}` for deterministic smoke checks.
   - Seed 3 quiz questions via `scripts/init_quiz_db.py` into `app/data/quiz.sqlite3`.
   - Render one intentionally plain quiz page in `app/templates/index.html`.
   - Provide endpoints for loading questions and receiving answer/skip actions.

3. **Add browser beacon logging and raw JSONL spool**
   - Add `app/static/beacon.js` using `navigator.sendBeacon` with `fetch` fallback.
   - Add `/beacon` endpoint that validates the minimum event contract, adds server timestamp/request metadata, and appends newline-delimited JSON to `data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl`.
   - Include event types: `page_view`, `answer_submitted`, and `question_skipped`; answer events carry `is_correct`.

4. **Implement MinIO raw upload step**
   - Add `scripts/upload_logs_to_minio.py` to upload JSONL spool files to `s3://raw/beacon-events/dt=YYYY-MM-DD/...`.
   - Keep object paths partition-like and documented.
   - Add README verification using MinIO console and/or `mc ls` inside the Compose network.

5. **Implement DuckDB loading/query step**
   - Add `scripts/load_minio_to_duckdb.py` that downloads/reads MinIO raw JSONL and creates `warehouse/quiz.duckdb` with a `raw_beacon_events` table.
   - Prefer deterministic Python loading for the beginner path; optionally include a docs note about DuckDB `httpfs`/S3 direct reads as an extension.

6. **Create dbt project on DuckDB**
   - Add `dbt_quiz/` with `dbt-duckdb` profile example targeting `warehouse/quiz.duckdb`.
   - Add `sources.yml` for `main.raw_beacon_events`.
   - Add staging model to cast timestamps, normalize event type, and expose event payload fields.
   - Add marts for quiz events and a simple summary table.
   - Add dbt tests for `event_id` uniqueness/non-null, accepted event types, and non-null timestamps.

7. **Add provided final visualization**
   - Add `scripts/render_report.py` that reads dbt output from DuckDB and writes a self-contained static HTML report under `reports/quiz_pipeline_report.html`.
   - Include simple charts/tables for event counts by type, correct vs incorrect submissions, and skip count by question.
   - Do not make chart creation a learner design exercise.

8. **Write README and docs**
   - Make `README.md` the Korean step-by-step main lab with copy/paste commands and checkpoints.
   - Include architecture diagram, checkpoints, reset/troubleshooting, and “what you learned” sections.
   - Add `docs/` conceptual reading material for DE vs analytics engineering, event design, A/B test extensions, and architecture variants.

9. **Add verification, smoke tests, and guided replay**
   - Add `scripts/verify_pipeline.py` to assert files/services/tables/report exist and contain expected rows.
   - `verify_pipeline.py` must explicitly check: SQLite has exactly 3 questions; required event types (`page_view`, `answer_submitted`, `question_skipped`) exist; minimum fields (`event_id`, `schema_version`, `session_id`, `anonymous_user_id`, timestamps, and `is_correct` for answer events) are populated; both correct and incorrect answer outcomes are represented after sample events.
   - Add `scripts/run_full_pipeline.sh` as a post-lesson replay wrapper after the manual lesson steps: upload -> DuckDB load -> dbt run -> dbt test -> report -> verify. It is convenience automation, not the primary learning path.
   - Add optional pytest tests if the implementation already has a test dependency; otherwise keep verification dependency-free.
   - Document both manual checkpoints and the final one-command replay in README.

## Acceptance Criteria

1. `docker compose up -d minio createbuckets web` starts MinIO and the quiz app without manual service edits.
2. `http://localhost:8000` shows exactly 3 seed quiz questions from SQLite.
3. Visiting the quiz page creates at least one `page_view` beacon row in local JSONL spool.
4. Answer submission creates `answer_submitted` events with `is_correct=true/false` and required minimum fields populated.
5. Skipping a question creates `question_skipped` events with required minimum fields populated.
6. Upload script places raw JSONL files under a documented MinIO bucket/path.
7. DuckDB load script creates `warehouse/quiz.duckdb` and a queryable `raw_beacon_events` table.
8. `dbt run` succeeds against DuckDB and creates staging/mart models.
9. `dbt test` succeeds for non-null, uniqueness, and accepted-values checks.
10. Report script creates `reports/quiz_pipeline_report.html` with non-empty values derived from dbt output.
11. README includes checkpoint commands for app, local spool, MinIO, DuckDB, dbt, and report, followed by `scripts/run_full_pipeline.sh` as a guided replay wrapper.
12. `docs/` includes analytics-engineering boundary material without moving that curriculum into the main README.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Too many moving parts for beginners | Use Option A with explicit scripts and checkpoints; avoid collector service. |
| MinIO/S3 details distract from DE blueprint | Provide fixed local credentials and partition path; keep S3 theory short. |
| dbt profile path confusion | Use a repository-local `profiles.yml.example` and README commands that set `DBT_PROFILES_DIR`. |
| Visualization becomes analytics lesson | Keep it as generated static HTML with no chart design task. |
| Empty or missing events during verification | Add `scripts/generate_sample_events.py` so learners can seed events if browser steps fail. |
| DuckDB direct S3 setup is fragile | Use Python-mediated loading for core path; document direct S3 as optional extension only. |

## Verification Steps

1. `docker compose config` validates Compose syntax.
2. `docker compose build` builds `web` and `pipeline` images.
3. `docker compose up -d minio createbuckets web` starts local services with default `WEB_PORT=8000`.
4. `curl http://localhost:8000/health` returns JSON `{"status":"ok"}`.
5. `docker compose run --rm pipeline python -c "import sqlite3; print(sqlite3.connect('/workspace/app/data/quiz.sqlite3').execute('select count(*) from questions').fetchone()[0])"` prints `3`.
6. Browser activity or `scripts/generate_sample_events.py` creates JSONL under `data/raw_spool/`.
7. A JSONL/DuckDB verification query proves required event types exist: `page_view`, `answer_submitted`, and `question_skipped`.
8. A verification query proves required fields are populated: `event_id`, `schema_version`, `session_id`, `anonymous_user_id`, `occurred_at_client`, `received_at_server`, `event_type`, plus `is_correct` for answer events.
9. `docker compose run --rm pipeline python scripts/upload_logs_to_minio.py` uploads to MinIO under `s3://raw/beacon-events/dt=YYYY-MM-DD/`.
10. `docker compose run --rm pipeline python scripts/load_minio_to_duckdb.py` creates `warehouse/quiz.duckdb` and `raw_beacon_events`.
11. `docker compose run --rm pipeline dbt --project-dir dbt_quiz --profiles-dir dbt_quiz run` succeeds.
12. `docker compose run --rm pipeline dbt --project-dir dbt_quiz --profiles-dir dbt_quiz test` succeeds.
13. `docker compose run --rm pipeline python scripts/render_report.py` writes `reports/quiz_pipeline_report.html`.
14. `docker compose run --rm pipeline bash scripts/run_full_pipeline.sh` succeeds as a guided replay wrapper.
15. `docker compose run --rm pipeline python scripts/verify_pipeline.py` passes and prints a concise evidence summary.

## ADR

### Decision

Use a Flask quiz app with local JSONL log spool, explicit learner-run pipeline scripts for MinIO upload and DuckDB loading, dbt-on-DuckDB transformations, and a generated static HTML report.

### Drivers

- Beginner comprehension of data-engineering boundaries.
- Deterministic copy/paste README flow.
- Required stack: SQLite, MinIO, DuckDB, dbt.

### Alternatives Considered

- Direct app-to-MinIO writes.
- Separate collector service.
- Full dashboard framework such as Streamlit/Superset/Metabase.

### Why Chosen

The chosen design exposes the full data path without adding production-grade infrastructure that would distract from the learning goal.

### Consequences

- Learners run multiple manual pipeline commands.
- The lab is batch-oriented rather than streaming/real-time.
- The visualization is intentionally basic.

### Follow-ups

- Add optional docs extension for direct DuckDB S3 reads.
- Add optional docs extension for production collector service architecture.
- Add optional docs extension for analytics-engineering event design and A/B test modeling.

## Available-Agent-Types Roster

Known useful agent types for execution follow-up:

- `executor` — implementation/refactoring; use high reasoning for cross-file feature work.
- `test-engineer` — test strategy, smoke checks, and regression coverage; medium reasoning.
- `writer` — README/docs and Korean learning flow; high reasoning for pedagogy and clarity.
- `verifier` — final evidence collection and completion validation; high reasoning.
- `build-fixer` — Docker/package/dbt failure resolution if verification fails; high reasoning.
- `code-reviewer` — comprehensive review before final handoff; high reasoning.

## Follow-up Staffing Guidance

### `$ralph` path

- Recommended for a single persistent owner after this plan.
- Suggested sequence:
  1. `executor` (high): implement app, Compose, pipeline, dbt, report.
  2. `test-engineer` (medium): add verification scripts/checkpoints once core files exist.
  3. `writer` (high): polish Korean README and `docs/` after behavior stabilizes.
  4. `verifier` (high): run full evidence pass and identify gaps.
- Use `build-fixer` only if Docker/dbt/package failures block verification.

### `$team` path

- Recommended if implementing in parallel with 4 lanes:
  1. App/beacon lane — `executor` high: Flask, SQLite, templates, JS beacon, event spool.
  2. Pipeline lane — `executor` high: MinIO upload, DuckDB load, dbt project/models/tests.
  3. Docs lane — `writer` high: README, docs boundary material, troubleshooting.
  4. Verification lane — `test-engineer` medium + later `verifier` high: smoke scripts and evidence.
- Optional final `code-reviewer` high pass before delivery.

### Pre-execution Plan Gate

Before invoking `$ralph` or `$team`, these planning artifacts must exist:

- `.omx/plans/plan-data-pipeline-hands-on-beacon-logs.md`
- `.omx/plans/prd-data-pipeline-hands-on-beacon-logs.md`
- `.omx/plans/test-spec-data-pipeline-hands-on-beacon-logs.md`

### Launch Hints

```bash
$ralph .omx/plans/plan-data-pipeline-hands-on-beacon-logs.md
$team .omx/plans/plan-data-pipeline-hands-on-beacon-logs.md
omx team --task "Implement .omx/plans/plan-data-pipeline-hands-on-beacon-logs.md with app, pipeline, docs, and verification lanes"
```

Team verification should prove app events, exact 3-question SQLite seed, minimum event contract, shared spool volume, MinIO upload, DuckDB/dbt output, report generation, guided replay, and README checkpoint accuracy before shutdown. Ralph follow-up should re-run the complete verification sequence and close any gaps.


## Draft Revision Changelog

- Applied Architect feedback: added guided replay wrapper, explicit shared volume/path contract, minimum event schema, exact 3-question acceptance criterion, and concrete staffing roster/counts/reasoning guidance.


## Draft Revision Changelog v3

- Applied Critic feedback: added `scripts/run_full_pipeline.sh` to file tree, explicit `/health` app contract, `WEB_PORT=8000`, exact SQLite/event-field verification checks, and explicit PRD/test-spec pre-execution gate.


## Draft Revision Changelog v4

- Applied Architect re-review polish: made pipeline access to `app/data` explicit, required deterministic sample events for correct/incorrect/skip/page_view cases, and clarified `run_full_pipeline.sh` as post-lesson replay automation.


## Consensus Review Changelog

- Architect iteration 1 requested a clearer guided replay path, shared storage contract, minimum event contract, and staffing guidance; these were applied in draft v2.
- Critic iteration 1 requested `scripts/run_full_pipeline.sh` in the file tree, an explicit `/health` contract, exact 3-question/event-field verification, PRD/test-spec gate, and concrete `WEB_PORT=8000`; these were applied in draft v3.
- Architect iteration 2 approved after minor polish: pipeline access to `app/data`, deterministic sample-event cases, and post-lesson replay wording; these were applied in draft v4.
- Critic iteration 2 approved v4 with no critical improvements required.
