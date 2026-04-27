# Final Consensus Plan: Data Pipeline Hands-on Curriculum Reorganization

## Consensus Status

- Status: APPROVED by final Critic review
- Finalized UTC: 2026-04-27T00:00:00Z
- Context snapshot: `.omx/context/handson-curriculum-restructure-access-logs-20260427T025733Z.md`
- PRD: `.omx/plans/prd-curriculum-reorg-data-pipeline-hands-on.md`
- Test spec: `.omx/plans/test-spec-curriculum-reorg-data-pipeline-hands-on.md`

## Requirements Summary

Reorganize the curriculum so the README teaches the data-pipeline story in the user-requested order, without discarding current in-progress work. The new structure must begin with:

1. 소개
   1.1 왜 데이터 파이프라인이 필요한가?
   1.2 데이터 보존 환경은 어떤 것이 있는지
2. 데이터 환경 구축 그리고 데이터 확인
   2.1 환경 셋업
   2.2 데이터를 확인하고 분석 해보기
      - DWH 데이터 확인
      - DataLake 데이터 확인
      - 어플리케이션 데이터 확인하기
      - 데이터 발생지점 확인하기
3. 데이터의 연계: 데이터 레이크에 저장된 데이터를 데이터 웨어하우스로 연계
4. 분석 요건에 맞춰 액세스 로그 추가하기

Then add the remaining phases, explain what each phase teaches, and add concrete copy/paste DuckDB queries and dbt configuration/modeling tasks where they improve learning. The result should be curriculum-first but still implementable through `README.md`, `docs/`, `dbt_quiz/`, `scripts/`, and targeted `app/` adjustments.

## Grounded Repository Facts

- `README.md` currently contains the stack mapping in lines ~64-122 and the step-by-step hands-on flow from roughly line 233 onward.
- The current README hands-on sequence is operationally correct but is ordered as build/run/generate/load/model/report rather than the requested curriculum-first story.
- `app/static/beacon.js` currently emits `page_view`, `answer_submitted`, and `question_skipped`.
- `app/app.py` validates those event types and appends JSONL raw logs, enriching them with `received_at_server` and `server_metadata`.
- Raw landing and transport are already script-driven through `scripts/upload_logs_to_minio.py` and `scripts/load_minio_to_duckdb.py`.
- The dbt project already contains `stg_beacon_events`, `fct_quiz_events`, `mart_quiz_summary`, and supporting summary marts/tests under `dbt_quiz/`.
- `docs/web-beacon-logs.md` is newly added and should be preserved; current working tree also has uncommitted changes in `README.md`, `app/static/beacon.js`, and `app/templates/index.html`.

## RALPLAN-DR Summary

### Principles

1. **Curriculum order beats implementation order**: the README should follow the learner’s mental model first, then explain how the repository realizes it.
2. **Observation before automation**: every phase should let learners inspect a concrete artifact before moving to the next layer.
3. **Preserve existing working boundaries**: avoid redesigning the architecture when reordering explanation and adding targeted curriculum support is enough.
4. **Use current repository primitives**: prefer README/docs/dbt/scripts/app adjustments over new services or dependencies.
5. **Teach the contract, not just the commands**: every phase should name what data exists, where it lives, why it exists, and how to verify it.

### Top Decision Drivers

1. **Requested learning order fidelity**: the README must match the user’s curriculum order, not merely rename existing sections.
2. **Low-risk compatibility with current code and uncommitted edits**: the plan must not require clobbering the current README/UI/docs work.
3. **Hands-on clarity**: learners need inspectable queries, file paths, and dbt tasks that make each storage boundary visible.

### Viable Options

#### Option A — README-only reordering, keep code and data flow unchanged

- **Approach**: Rewrite headings and cross-links in `README.md`, but leave scripts/app/dbt behavior largely unchanged.
- **Pros**:
  - Lowest implementation risk.
  - Fastest way to satisfy the requested outline.
  - Minimizes merge pressure on current uncommitted app/UI changes.
- **Cons**:
  - Phase 2 becomes weak because learners are asked to inspect DWH/DataLake data before the README gives them a natural way to materialize or browse both.
  - Phase 4 “액세스 로그 추가하기” risks being only narrative, because current access-style fields are limited to the existing beacon payload.

#### Option B — Curriculum-first bootstrap path with sample inspection artifacts (favored)

- **Approach**: Reorder the README around the requested phases and add a small “observation bootstrap” path: learners can inspect pre-generated or script-generated raw/DWH artifacts in Phase 2, then rebuild/understand the actual lake-to-warehouse linkage in Phase 3, then extend access-log fields in Phase 4.
- **Pros**:
  - Best fit for the requested order without lying about system behavior.
  - Lets Phase 2 include concrete DuckDB/MinIO/app inspections before deep implementation steps.
  - Reuses existing scripts (`generate_sample_events.py`, upload/load, dbt) with modest README and verification enhancements.
- **Cons**:
  - Requires careful README wording so “sample inspection” is not confused with the learner’s own pipeline output.
  - Needs small script/dbt/report touchups for an exact Phase 4 access-log slice: `quiz_step`, `display_order`, `mart_access_log_funnel`, and a report section.

#### Option C — Introduce a separate seeded warehouse snapshot for curriculum navigation

- **Approach**: Commit a maintained demo DuckDB/MinIO snapshot purely for early curriculum browsing.
- **Pros**:
  - Makes Phase 2 very easy to demo.
  - Reduces setup friction for inspection-first learners.
- **Cons**:
  - Adds artifact maintenance burden and risk of stale snapshots.
  - Blurs the line between repository source-of-truth and generated outputs.
  - Less attractive because the repo already contains scripts that can generate observation data on demand.

### Favored Option

Choose **Option B**.

It best satisfies the requested curriculum order while staying close to the existing repository structure. The implementation should treat Phase 2 as an **inspection bootstrap**: learners first stand up the environment and inspect app/data-lake/DWH artifacts using deterministic sample data or guided bootstrap commands. Phase 3 then teaches the actual data-lake-to-warehouse linkage as a repeatable mechanism. Phase 4 extends the event contract to meet analysis needs, using the existing beacon flow rather than introducing a separate logging system.

## Concrete Curriculum Plan

### Phase 1. 소개

#### 1.1 왜 데이터 파이프라인이 필요한가?
**What it teaches**
- Why application data alone is not enough for analysis.
- Why raw logs, durable storage, analytical storage, and modeled datasets exist as separate layers.
- How this repo maps “서비스 행동 → Raw 저장 → 적재 → 모델링 → 리포트”.

**README changes**
- Move or adapt current goal/architecture material near the top.
- Keep the current stack table (`README.md` around lines 64-122) but reframe it under “파이프라인이 필요한 이유” instead of presenting it before the learning story.
- Add a concise before/after diagram showing: application DB vs raw object storage vs warehouse vs dbt marts.

**Useful additions**
- Link `docs/pipeline-architecture.md` as optional depth.
- Add a “이 단계에서 구분해야 할 저장소” callout:
  - SQLite = application/OLTP
  - MinIO = DataLake/raw zone
  - DuckDB = DWH/analytical store
  - dbt marts = analysis-ready model

### Phase 1.2 데이터 보존 환경은 어떤 것이 있는지
**What it teaches**
- Differences among application DB, raw spool, object storage, warehouse, and modeled marts.
- The “why” behind each persistence boundary.

**README changes**
- Split the current tech-stack table into a learner-facing storage comparison subsection.
- Explicitly map local spool and MinIO to “DataLake-like raw preservation” and DuckDB to “DWH-like consumption layer”.

**Useful additions**
- Add a small comparison matrix with columns: 저장 목적 / 쓰기 주체 / 읽는 사람 / 예시 파일 or table.
- Point learners to `docs/data-engineering-vs-analytics-engineering.md` for scope boundaries.

---

### Phase 2. 데이터 환경 구축 그리고 데이터 확인

#### 2.1 환경 셋업
**What it teaches**
- How to bring up the local environment safely.
- Which folders/files become the hands-on checkpoints.

**README changes**
- Reuse current Compose/app startup content.
- Keep reset instructions, but move them into a clearly labeled prerequisite/setup block.
- Add an explicit **single bootstrap contract**: Phase 2 is allowed to pre-materialize inspectable artifacts by running the full deterministic path once — sample events → MinIO upload → DuckDB load → dbt run/test — only so learners can browse all layers before Phase 3 reteaches the same path step by step.

**Concrete bootstrap commands to surface**
- `docker compose up -d minio createbuckets web`
- `docker compose run --rm pipeline python scripts/init_quiz_db.py`
- `export BOOTSTRAP_DATE=$(date -u +%F)`
- `docker compose run --rm pipeline python scripts/generate_sample_events.py --date "$BOOTSTRAP_DATE" --overwrite`
- `docker compose run --rm pipeline python scripts/upload_logs_to_minio.py`
- `docker compose run --rm pipeline python scripts/load_minio_to_duckdb.py`
- `docker compose run --rm pipeline dbt run --project-dir dbt_quiz --profiles-dir dbt_quiz`
- `docker compose run --rm pipeline dbt test --project-dir dbt_quiz --profiles-dir dbt_quiz`
- Optional helper wrapper if introduced later: `scripts/bootstrap_observation_data.sh` (only if the implementer decides the README would otherwise be too verbose; not required by the plan)

#### 2.2 데이터를 확인하고 분석 해보기

##### 2.2.a DWH 데이터 확인
**What it teaches**
- What warehouse tables look like after raw events become SQL-accessible.
- Difference between raw table, staging, fact, and mart.
- That Phase 2 DWH inspection depends on the one-time bootstrap path, not on magic preexisting warehouse state.

**Repository touchpoints**
- `README.md`
- `scripts/load_minio_to_duckdb.py`
- `dbt_quiz/dbt_project.yml`
- `dbt_quiz/models/staging/stg_beacon_events.sql`
- `dbt_quiz/models/marts/fct_quiz_events.sql`
- `dbt_quiz/models/marts/mart_quiz_summary*.sql`

**Copy/paste DuckDB inspection command to include**
```bash
docker compose run --rm pipeline python - <<'PY'
import duckdb
queries = {
    "raw event count": "select count(*) as raw_events from raw_beacon_events",
    "raw events by type": "select event_type, count(*) as cnt from raw_beacon_events group by 1 order by 1",
    "staging preview": "select event_id, event_type, question_id, received_at_server from stg_beacon_events order by received_at_server limit 5",
    "summary mart": "select metric_name, metric_value from mart_quiz_summary order by metric_name",
}
with duckdb.connect('/workspace/warehouse/quiz.duckdb', read_only=True) as conn:
    for label, sql in queries.items():
        print(f"\n-- {label}")
        for row in conn.execute(sql).fetchall():
            print(row)
PY
```

**dbt configuration tasks to include**
- Explain `dbt_quiz/dbt_project.yml` materialization defaults.
- Show how `schema.yml` enforces event-type and not-null tests.
- Add a short learner task: run `dbt run` and `dbt test`, then explain what changed in DuckDB.

##### 2.2.b DataLake 데이터 확인
**What it teaches**
- Raw landing format and partition-like object layout.
- Why raw preservation precedes transformation.

**Repository touchpoints**
- `README.md`
- `data/raw_spool/beacon_events/...`
- `scripts/upload_logs_to_minio.py`
- `docs/web-beacon-logs.md`

**Inspection tasks**
- Open JSONL locally.
- Verify MinIO object key layout under `beacon-events/dt=YYYY-MM-DD/...`.
- Compare a raw event row with warehouse columns.

**Copy/paste DataLake inspection commands to include**
```bash
find data/raw_spool/beacon_events -type f | sort
sed -n '1,5p' data/raw_spool/beacon_events/dt=$BOOTSTRAP_DATE/events.jsonl

docker compose run --rm --entrypoint /bin/sh createbuckets -c '
mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
mc ls local/raw/beacon-events/ --recursive
'
```
Also keep the MinIO Web UI path: `http://localhost:9001` → Object Browser → `raw/beacon-events/dt=$BOOTSTRAP_DATE/events.jsonl`. The README must define and reuse one `BOOTSTRAP_DATE` variable so UTC sample generation and local inspection always point at the same partition.

##### 2.2.c 어플리케이션 데이터 확인하기
**What it teaches**
- Operational product data vs analytics/event data.
- Why quiz questions live in SQLite and not in the warehouse raw event table.

**Repository touchpoints**
- `README.md`
- `app/app.py`
- `app/data/quiz.sqlite3`
- `app/quiz_seed.py`

**Copy/paste SQLite inspection task**
```bash
docker compose run --rm pipeline python - <<'PY'
import sqlite3
with sqlite3.connect('/workspace/app/data/quiz.sqlite3') as conn:
    rows = conn.execute('select id, prompt, correct_choice from questions order by id').fetchall()
for row in rows:
    print(row)
PY
```

##### 2.2.d 데이터 발생지점 확인하기
**What it teaches**
- Where user behavior becomes an event.
- Which client/server functions form the source of truth.

**Repository touchpoints**
- `app/static/beacon.js`
- `app/app.py`
- `docs/web-beacon-logs.md`

**Code-reading checkpoints**
- `baseEvent(...)`
- `showQuestion(...)`
- `submitAnswer(...)`
- `skipQuestion(...)`
- `validate_event(...)`
- `spool_event(...)`

---

### Phase 3. 데이터의 연계: 데이터 레이크에 저장된 데이터를 데이터 웨어하우스로 연계

**What it teaches**
- The actual transport/loading path from raw object storage to analytical tables.
- Why “inspect first” and “build the linkage” are different learning moments.

**Primary repository touchpoints**
- `README.md`
- `scripts/upload_logs_to_minio.py`
- `scripts/load_minio_to_duckdb.py`
- `warehouse/quiz.duckdb`
- `dbt_quiz/models/...`
- `scripts/verify_pipeline.py`

**Concrete tasks**
1. Re-run the same deterministic path used for Phase 2 bootstrap, but this time explain each handoff explicitly: raw spool → MinIO → DuckDB raw table → dbt models.
2. Upload raw spool files to MinIO.
3. Load MinIO objects into `raw_beacon_events` in DuckDB.
4. Run dbt staging/fact/mart models.
5. Compare the same business event across raw JSONL, `raw_beacon_events`, and `stg_beacon_events`.

**DuckDB/dbt tasks to highlight**
- Explain how `source_object_key` and `loaded_at` support traceability.
- Show a query comparing raw and modeled layers:
```sql
select event_type, count(*) from raw_beacon_events group by 1 order by 1;
select event_type, count(*) from fct_quiz_events group by 1 order by 1;
```
- Include a learner prompt to inspect `schema.yml` and identify which constraints protect the event contract.

**Why this phase matters in the plan**
- It resolves the ordering tension by making Phase 2 a single, transparent bootstrap for inspection and Phase 3 the explicit reconstruction/explanation of the same path.

---

### Phase 4. 분석 요건에 맞춰 액세스 로그 추가하기

**What it teaches**
- Analytics requirements change event contracts.
- An access log can be represented as enriched `page_view` beacon events in this lab.
- The correct implementation target is not “more logging everywhere,” but one analysis question → exact fields → exact warehouse/dbt/report artifacts.

**Planning decision**
- Treat `page_view` as the access-log event type. Do **not** add a separate web-server/Nginx-style access log subsystem.
- Extend `page_view`, `answer_submitted`, and `question_skipped` with one exact question-progression field set so learners can analyze where a session viewed, answered, or skipped.
- Make `quiz_step` meaningful by emitting access views for three screen/step states: `landing`, `question`, and `finish`. This avoids the previous weak single-value `quiz_step='question'` contract.

**Exact Phase 4 field contract**

| Field | Applies to | Type/values | Semantics |
| --- | --- | --- | --- |
| `quiz_step` | all `page_view`, `answer_submitted`, and `question_skipped` rows | one of `landing`, `question`, `finish` for `page_view`; required value `question` for `answer_submitted` and `question_skipped` | screen or quiz step where the event happened |
| `display_order` | all question-scoped `page_view`, `answer_submitted`, and `question_skipped` rows | integer, 1-based, null only for non-question rows such as `landing` and `finish` | per-session order in which a question was displayed; answer/skip rows must carry the same value as their displayed question |

**Exact deterministic sample/browser event sequence**

The Phase 4 implementation must make the sample generator produce this minimum sequence for one session:

| Order | Event | quiz_step | question_id | display_order | Expected purpose |
| --- | --- | --- | --- | --- | --- |
| 1 | `page_view` | `landing` | null | null | user accessed the quiz landing screen |
| 2 | `page_view` | `question` | first seeded question ID | 1 | first displayed question |
| 3 | `answer_submitted` | `question` | first seeded question ID | 1 | correct answer path |
| 4 | `page_view` | `question` | second seeded question ID | 2 | second displayed question |
| 5 | `answer_submitted` | `question` | second seeded question ID | 2 | incorrect answer path |
| 6 | `page_view` | `question` | third seeded question ID | 3 | third displayed question |
| 7 | `question_skipped` | `question` | third seeded question ID | 3 | skip path |
| 8 | `page_view` | `finish` | null | null | user reached the finish screen |

The live browser path should match the same semantics even if the concrete seeded question ID order is randomized by UI state.

**Exact downstream artifacts**

Phase 4 must create/update these exact artifacts:

- DuckDB raw table columns in `scripts/load_minio_to_duckdb.py`:
  - `quiz_step VARCHAR`
  - `display_order BIGINT`
- dbt staging/fact exposure:
  - `dbt_quiz/models/staging/stg_beacon_events.sql` exposes `quiz_step`, `display_order`
  - `dbt_quiz/models/marts/fct_quiz_events.sql` carries `quiz_step`, `display_order`
- New exact mart:
  - `dbt_quiz/models/marts/mart_access_log_funnel.sql`
  - Required columns: `quiz_step`, `display_order`, `view_count`, `answer_count`, `skip_count`, `session_count`
- `dbt_quiz/models/schema.yml` tests:
  - `quiz_step` accepted values: `landing`, `question`, `finish` for rows where it is not null
  - `display_order` not null on rows where `event_type in ('page_view', 'answer_submitted', 'question_skipped') and quiz_step = 'question'`
- `scripts/render_report.py` adds a non-optional section titled `접속/문항 노출 퍼널` backed by `mart_access_log_funnel`
- `scripts/verify_pipeline.py` asserts:
  - sample/browser data contains `page_view` rows for `landing`, `question`, and `finish`
  - question-scoped events have display orders 1, 2, 3 in sample data
  - all `answer_submitted` rows have `quiz_step='question'`
  - all `question_skipped` rows have `quiz_step='question'`
  - all `answer_submitted` and `question_skipped` rows have non-null `display_order`
  - deterministic sample answer rows carry display orders 1 and 2, and the deterministic sample skip row carries display order 3
  - `mart_access_log_funnel` exists and has nonzero `view_count`
  - `reports/quiz_pipeline_report.html` contains the exact section title `접속/문항 노출 퍼널`

**Functions likely to change if Phase 4 is implemented**
- page initialization in `app/static/beacon.js`: emit `page_view` with `quiz_step='landing'` once when the landing panel is shown.
- `showQuestion(...)`: emit `page_view` with `quiz_step='question'` and `display_order = state.orderIndex + 1`.
- `submitAnswer(...)` and `skipQuestion(...)`: carry `quiz_step='question'` and the same `display_order` as the displayed question.
- `showFinish()`: emit `page_view` with `quiz_step='finish'`.
- `app/app.py`: no new event type is required. Server validation remains intentionally minimal: it validates common fields and event type only. The Phase 4 access-log contract is enforced by deterministic sample generation, DuckDB/dbt exposure, dbt tests, and `scripts/verify_pipeline.py` assertions—not by rejecting partial browser payloads at `/beacon`.

**Exact dbt mart sketch**
```sql
select
  quiz_step,
  display_order,
  count(*) filter (where event_type = 'page_view') as view_count,
  count(*) filter (where event_type = 'answer_submitted') as answer_count,
  count(*) filter (where event_type = 'question_skipped') as skip_count,
  count(distinct session_id) as session_count
from {{ ref('fct_quiz_events') }}
where quiz_step is not null
group by 1, 2
order by display_order nulls first, quiz_step
```

**README exercise to add**
```bash
docker compose run --rm pipeline python - <<'PY'
import duckdb
with duckdb.connect('/workspace/warehouse/quiz.duckdb', read_only=True) as conn:
    for row in conn.execute('''
        select quiz_step, display_order, view_count, answer_count, skip_count, session_count
        from mart_access_log_funnel
        order by display_order nulls first, quiz_step
    ''').fetchall():
        print(row)
PY
```

**Fields to avoid unless a concrete question requires them**
- Broad `page_name` / `screen_name` fields not used by a README query.
- Infrastructure request fields such as status code or response bytes; these belong to a separate optional server-access-log extension.

---

### Remaining Phases to Add After the Requested Four

#### Phase 5. dbt로 분석용 데이터 모델 만들기
**What it teaches**
- Why staging/fact/mart layers exist.
- How dbt codifies naming, tests, and reusable business logic.

**Touchpoints**
- `dbt_quiz/dbt_project.yml`
- `dbt_quiz/models/schema.yml`
- `dbt_quiz/models/staging/*.sql`
- `dbt_quiz/models/marts/*.sql`

**Tasks**
- Explain source vs model refs.
- Add a short “modify or add one mart” exercise tied to access-log analysis.
- Keep advanced analytics theory in `docs/`, not the main README.

#### Phase 6. 검증과 리포트 생성
**What it teaches**
- A pipeline is not done when it runs; it is done when it proves correctness.

**Touchpoints**
- `scripts/verify_pipeline.py`
- `scripts/render_report.py`
- `reports/quiz_pipeline_report.html`
- `dbt_quiz/models/schema.yml`

**Tasks**
- Run `dbt test` and `verify_pipeline.py`.
- Open the HTML report and tie metrics back to raw events and marts.
- Phase 4 must extend the report with one dedicated access-log section titled `접속/문항 노출 퍼널` backed by `mart_access_log_funnel`.

#### Phase 7. 전체 파이프라인 재실행과 확장 읽기
**What it teaches**
- Reproducibility, replay, and where to go next.

**Touchpoints**
- `scripts/run_full_pipeline.sh`
- `docs/pipeline-architecture.md`
- `docs/data-engineering-vs-analytics-engineering.md`
- `docs/event-design-and-ab-testing.md`
- `docs/web-beacon-logs.md`

**Tasks**
- Re-run the whole flow in one shot.
- Contrast manual learning path vs automation wrapper.
- Link to extension ideas without bloating the core README.

## File Touchpoint Plan

### Primary edits
- `README.md`
  - Major heading/order reorganization.
  - New phase summaries and learning objectives.
  - New inspection queries/commands.
  - Clear separation between observation bootstrap (Phase 2) and linkage build (Phase 3).
- `docs/web-beacon-logs.md`
  - Align terminology so “웹 비콘 로그” and “액세스 로그” are consistent.
  - Document any new page/access analysis fields.
- `docs/pipeline-architecture.md`
  - Update narrative so the curriculum order is reflected even if runtime order differs.

### Secondary likely edits
- `scripts/generate_sample_events.py`
  - Ensure deterministic sample events cover the exact Phase 4 sequence: landing view, three question views with display orders 1-3, two answers, one skip, finish view.
- `scripts/verify_pipeline.py`
  - Verify the new curriculum-critical artifacts, `mart_access_log_funnel`, `quiz_step`/`display_order`, answer/skip `quiz_step='question'`, non-null answer/skip `display_order`, deterministic answer/skip order values, and exact report section title `접속/문항 노출 퍼널`.
- `scripts/render_report.py`
  - Add the non-optional `접속/문항 노출 퍼널` report section backed by `mart_access_log_funnel`.
- `scripts/load_minio_to_duckdb.py`
  - Extend schema if Phase 4 adds fields.
- `dbt_quiz/models/staging/stg_beacon_events.sql`
  - Cast/expose added access-log columns.
- `dbt_quiz/models/schema.yml`
  - Add tests for access-log fields or new marts.
- `dbt_quiz/models/marts/mart_access_log_funnel.sql`
  - Add the exact access-log funnel mart with `quiz_step`, `display_order`, `view_count`, `answer_count`, `skip_count`, `session_count`.

### Preserve / do not clobber
- Existing uncommitted changes in `README.md`, `app/static/beacon.js`, `app/templates/index.html`, and `docs/web-beacon-logs.md` must be merged carefully, not overwritten.
- Execution must treat the dirty working tree as the baseline: edit in place, review diffs before large rewrites, and do not regenerate README/docs/app files wholesale.

## Acceptance Criteria

1. `README.md` is reorganized to follow the requested curriculum order exactly for the first four major phases.
2. Each major phase includes a short “what this phase teaches” summary.
3. Phase 2 contains concrete inspection tasks for DWH, DataLake, application data, and event generation points.
4. Phase 3 clearly teaches the lake-to-warehouse linkage using existing scripts and dbt models.
5. Phase 4 defines “액세스 로그” concretely as enriched `page_view` beacon logging with exact fields (`quiz_step`, `display_order`), exact sample sequence, exact mart (`mart_access_log_funnel`), exact report section (`접속/문항 노출 퍼널`), and verification assertions.
6. The README includes DuckDB queries and dbt configuration/modeling tasks where they improve understanding.
7. The core hands-on path remains README-first, while deeper theory stays in `docs/`.
8. No plan step requires overwriting the current uncommitted README/UI/docs changes.
9. Verification guidance covers both curriculum structure and data-pipeline correctness touchpoints.

## Risks and Mitigations

### Risk 1 — Requested order conflicts with current causal data flow
- **Mitigation**: Explicitly frame Phase 2 as observation/bootstrap and Phase 3 as mechanism/build linkage.

### Risk 2 — “액세스 로그” is interpreted as web-server access logging instead of product analytics events
- **Mitigation**: State in README/docs that this curriculum uses learner-facing page/access events built on the current beacon system; defer infrastructure access logging to optional extensions.

### Risk 3 — README expansion becomes too large and duplicates docs
- **Mitigation**: Keep README task-focused; move conceptual depth and alternatives into `docs/`.

### Risk 4 — Existing in-progress README/UI edits are accidentally lost during reorganization
- **Mitigation**: Require diff-aware merge sequencing and preserve current modified hunks before reflowing sections.

## Verification Plan

### Curriculum verification
- Confirm the first four top-level README phases match the requested order and wording.
- Confirm each phase has learning objectives plus at least one inspectable artifact/command.
- Confirm remaining phases are present and summarized.

### Data-path verification
- Confirm README commands still align with:
  - `scripts/generate_sample_events.py`
  - `scripts/upload_logs_to_minio.py`
  - `scripts/load_minio_to_duckdb.py`
  - `dbt_quiz` model names
  - `scripts/render_report.py`
  - `scripts/verify_pipeline.py`

### Access-log verification
- Verify Phase 4 end-to-end:
  - sample events include `quiz_step` values `landing`, `question`, `finish`,
  - question-scoped sample events include `display_order` values 1, 2, 3,
  - DuckDB `raw_beacon_events` loads `quiz_step` and `display_order`,
  - dbt exposes `quiz_step` and `display_order` in staging/fact models,
  - `mart_access_log_funnel` exists and has nonzero `view_count`
  - `reports/quiz_pipeline_report.html` contains the exact section title `접속/문항 노출 퍼널`,
  - `scripts/render_report.py` renders the `접속/문항 노출 퍼널` section.

### Regression verification
- `docker compose config`
- sample event generation
- upload/load/dbt/report/verify pipeline commands referenced in README
- spot check that existing `page_view`, `answer_submitted`, `question_skipped` coverage still holds

## ADR

### Decision
Adopt a **curriculum-first reorganization with observation bootstrap**, preserving the current pipeline architecture and extending it only where necessary to support earlier inspection and access-log analysis.

### Drivers
- Match the user’s requested learning order.
- Keep the repository implementable with small, reviewable changes.
- Preserve current architecture and uncommitted improvements.

### Alternatives Considered
- **README-only reorder**: rejected as too shallow for Phase 2/4 learning goals.
- **Committed seeded warehouse snapshot**: rejected due to maintenance cost and stale-artifact risk.
- **Separate infrastructure access-log subsystem**: rejected as scope creep relative to the current beacon-based curriculum.

### Why Chosen
This option gives the clearest learner journey while minimizing code churn. It resolves the only major ordering conflict—inspecting DWH/DataLake before building the linkage—by introducing a transparent bootstrap/inspection concept rather than forcing an architectural rewrite.

### Consequences
- README work is substantial and should lead the implementation.
- Scripts/dbt/report/verifier pieces need the exact supporting changes named in Phase 4; avoid leaving mart/report/verification choices or enforcement boundary to executor interpretation. Server `/beacon` validation stays minimal; dbt/verifier owns Phase 4 contract enforcement.
- Terminology around “access log” must be explicit to avoid future confusion.

### Follow-ups
- Keep access-log fields minimal and analysis-driven.
- Avoid duplicating long theory sections in README.
- Preserve current modified hunks before large README section moves.

## Available Agent Types Roster

- `planner`: maintain plan integrity and sequencing
- `architect`: validate curriculum structure and storage-boundary coherence
- `critic`: challenge ordering, scope creep, and verification gaps
- `executor`: implement README/docs/script/dbt/app edits
- `writer`: polish Korean curriculum copy and docs boundaries
- `test-engineer`: shape README verification and command matrix
- `verifier`: confirm the final curriculum structure and referenced commands still match the repo
- `explore`: fast lookup of headings, file paths, and symbol locations during implementation

## Staffing Guidance

### Recommended Ralph path
- **Owner**: `executor`
- **Supporting review lanes**:
  - `writer` for README/docs wording pass
  - `verifier` for final evidence pass
- **Reasoning guidance**:
  - README restructuring: medium/high
  - dbt/script touchups: high
  - verification/report alignment: medium

### Recommended Team path
1. **Lane A — README curriculum restructure**
   - Agent: `executor` or `writer`
   - Ownership: `README.md`
2. **Lane B — docs terminology and curriculum support**
   - Agent: `writer`
   - Ownership: `docs/web-beacon-logs.md`, `docs/pipeline-architecture.md`
3. **Lane C — access-log support in app/scripts/dbt**
   - Agent: `executor`
   - Ownership: `app/static/beacon.js`, `app/app.py`, `scripts/*`, `dbt_quiz/models/*`
4. **Lane D — verification alignment**
   - Agent: `test-engineer` or `verifier`
   - Ownership: command matrix, `scripts/verify_pipeline.py`, acceptance proof

## Launch Hints

### Ralph-style sequential execution
- Suggested prompt:
  - `$ralph implement the approved curriculum reorganization plan in .omx/plans/plan-curriculum-reorg-data-pipeline-hands-on.md without overwriting current uncommitted README/UI/docs changes`

### Team-style parallel execution
- Suggested prompt:
  - `$team implement the approved curriculum reorganization plan from .omx/plans/plan-curriculum-reorg-data-pipeline-hands-on.md with lanes for README, docs, access-log/dbt support, and verification`
- Suggested lane order:
  1. README restructure first
  2. docs alignment second
  3. access-log/dbt/script support third
  4. final verification/report pass last

## Team Verification Path

1. Reconcile README headings against the approved curriculum order.
2. Verify every referenced command/path/model exists after edits.
3. Run the documented data-path verification commands.
4. If access-log fields/marts were added, verify them end-to-end from sample event generation to dbt/report output.
5. Confirm no current uncommitted user work was overwritten during the merge.

## Implementation Sequencing Recommendation

1. Stabilize and preserve current modified hunks.
2. Restructure `README.md` around the new phase order.
3. Align docs terminology and cross-links.
4. Only after README/docs structure is stable, add the minimal script/dbt/app support required for the explicit Phase 2 bootstrap and the exact Phase 4 access-log artifacts (`quiz_step`, `display_order`, `mart_access_log_funnel`, report section, verifier assertions).
5. Update verification/reporting to match the new curriculum.
6. Run final curriculum and pipeline verification.


## Consensus Revision Changelog

### Architect ITERATE improvements applied
- Pinned Phase 4 to exact artifacts: `mart_access_log_funnel`, report section `접속/문항 노출 퍼널`, and verifier assertions.
- Made `quiz_step` meaningful by expanding access-log semantics to `landing`, `question`, and `finish` page-view rows rather than a single `question` value.
- Defined a deterministic sample event sequence covering landing view, three question views, two answers, one skip, and finish view.
- Rewrote Phase 2 inspection snippets as copy/paste `docker compose run ... python - <<'PY'` commands in the current README style.
- Added explicit dirty-working-tree merge-safety guidance.

### Second Architect ITERATE text-tightening applied
- Made `quiz_step` and `display_order` mandatory on `answer_submitted` and `question_skipped` rows, not preferred.
- Added explicit verifier requirement for the report section title `접속/문항 노출 퍼널`.
- Replaced host `python3` `BOOTSTRAP_DATE` command with shell-only `date -u +%F`.
- Replaced q1/q2/q3 wording with first/second/third seeded question ID semantics.

### Critic ITERATE improvements applied
- Replaced stale host-Python bootstrap date in the test spec with `date -u +%F`.
- Added explicit verification requirements for answer/skip `quiz_step='question'`, non-null answer/skip `display_order`, and deterministic answer/skip order values.
- Chose the contract enforcement boundary explicitly: `/beacon` validation remains minimal; dbt tests and `verify_pipeline.py` enforce Phase 4 access-log semantics.


## Final Consensus Review Result

- Architect review: ITERATE twice; required improvements applied.
- Critic review: ITERATE once, then APPROVE.
- Final verdict: APPROVE.
- Final approval evidence: final Critic confirmed clarity, verifiability, completeness, principle/option consistency, alternatives depth, and risk/verification rigor all pass.
