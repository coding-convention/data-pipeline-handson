# Context Snapshot: Hands-on curriculum restructure + access log phase

## Task statement
User invoked `$ralplan` to revise the data engineering hands-on curriculum order. Desired sequence:
1. 소개
   1.1 왜 데이터 파이프라인이 필요한가?
   1.2 데이터 보존 환경은 어떤 것이 있는지
2. 데이터 환경 구축 그리고 데이터 확인
   2.1 환경 셋업
   2.2 데이터를 확인하고 분석 해보기: DWH 데이터 확인 / DataLake 데이터 확인 / 애플리케이션 데이터 확인 / 데이터 발생지점 확인
3. 데이터의 연계: 데이터 레이크에 저장된 데이터를 데이터 웨어하우스로 연계
4. 분석 요건에 맞춰 액세스 로그 추가하기
Then add the remaining structure, summarize what each phase teaches, and add DuckDB query/dbt configuration content where helpful.

## Desired outcome
A consensus-approved implementation plan for reorganizing README/docs and possibly code/dbt additions so the hands-on reads as a coherent curriculum with phases, learning objectives, inspection tasks, DuckDB SQL, and dbt configuration/modeling exercises.

## Known facts/evidence
- README currently starts with goal/architecture/tech stack table and a linear hands-on path, but does not yet follow the user's new four-part curriculum order exactly.
- README lines 64-122 already include technology stack and real-world mapping.
- README lines 124-159 include a step summary and key file table.
- README lines 300-470 cover compose startup, SQLite seed, browser beacon event generation, and raw spool inspection.
- app currently has Flask quiz with revised UI: `app/templates/index.html` starts on a main panel with `문제 풀기`, shows one question at a time, supports `답 제출`, `다음 문제`, `문제 패스`.
- `app/static/beacon.js` creates `page_view`, `answer_submitted`, `question_skipped` and sends to `/beacon`; page_view now occurs when a question is shown, not on initial page load.
- `app/app.py` accepts `/beacon`, validates common fields, appends JSONL with `received_at_server` and `server_metadata`.
- dbt current models: `stg_beacon_events`, `fct_quiz_events`, `mart_quiz_summary`, plus event/outcome/skip summary marts.
- Existing docs: `docs/data-engineering-vs-analytics-engineering.md`, `docs/event-design-and-ab-testing.md`, `docs/pipeline-architecture.md`, new untracked `docs/web-beacon-logs.md` explaining beacon logs.

## Constraints
- Planning only: `$ralplan` should stop after approved plan and not implement.
- Preserve previous user direction: analytics engineering deep-dive belongs under `docs/`, while README remains the main hands-on path.
- Current working tree has uncommitted edits from previous user requests: README.md, app/static/beacon.js, app/templates/index.html, docs/web-beacon-logs.md.
- Do not clobber uncommitted changes.
- Avoid new dependencies unless explicitly requested.

## Unknowns / open questions
- Whether “액세스 로그” should mean generic web server/request access logs, or product analytics access/page-view events. Reasonable plan should define it in curriculum and implement as a new phase with minimal beacon event extension, avoiding production web-server logging complexity.
- Whether final visualization should remain static HTML or get an extra access-log section. Plan should include a minimal static report extension.

## Likely touchpoints
- README.md: major curriculum reordering and phase descriptions.
- docs/web-beacon-logs.md: align access-log/page-view/access-event explanation.
- docs/pipeline-architecture.md and docs/event-design-and-ab-testing.md: optional references.
- app/static/beacon.js: potential new `access_log`/`question_viewed` style event or enrich `page_view` with access fields.
- app/app.py: event type validation if adding a new event type.
- scripts/generate_sample_events.py, scripts/verify_pipeline.py: sample and verification updates if event contract changes.
- scripts/load_minio_to_duckdb.py: schema updates if access fields added.
- dbt_quiz/models/staging/stg_beacon_events.sql and marts/schema/tests: new access-log mart or page-view/access model.
- scripts/render_report.py: optional new section.
