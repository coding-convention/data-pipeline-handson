# PRD: Data Pipeline Hands-on Curriculum Reorganization

## Problem

The repository already demonstrates the intended pipeline architecture, but the README teaches it in an implementation-order sequence rather than the user’s requested curriculum order. This makes the learning journey less intuitive for a learner who should first understand why the pipeline exists, then inspect each data environment, then build the linkage, and only then extend the access-log contract for analysis.

## Goal

Reorganize the hands-on curriculum so the first four top-level phases are:

1. 소개
2. 데이터 환경 구축 그리고 데이터 확인
3. 데이터의 연계: 데이터 레이크에 저장된 데이터를 데이터 웨어하우스로 연계
4. 분석 요건에 맞춰 액세스 로그 추가하기

Then add the remaining phases needed to complete the lab, while preserving the repository’s README-first hands-on character and existing architecture.

## Users

- Beginners learning data engineering from a local reproducible repository.
- Reviewers/maintainers who need the README and docs to match the actual repository behavior.

## Functional Requirements

| ID | Requirement |
|---|---|
| PRD-1 | `README.md` must adopt the requested first-four-phase order. |
| PRD-2 | Each phase must explain what the learner learns. |
| PRD-3 | Phase 2 must include a single explicit bootstrap path that materializes inspectable DWH, DataLake, application-data, and event-origin artifacts. |
| PRD-4 | Phase 3 must reteach the actual DataLake → DWH linkage step by step using repository scripts and dbt models. |
| PRD-5 | Phase 4 must define access-log work as enriched beacon `page_view` logging with exact fields (`quiz_step`, `display_order`), exact sample sequence, exact dbt mart (`mart_access_log_funnel`), exact report section (`접속/문항 노출 퍼널`), and exact verification assertions including answer/skip field semantics and the rendered report section title. |
| PRD-6 | DuckDB queries and dbt configuration/modeling tasks must be added where useful. |
| PRD-7 | README remains task-focused; deeper conceptual material belongs in `docs/`. |
| PRD-8 | Current uncommitted work in `README.md`, `app/static/beacon.js`, `app/templates/index.html`, and `docs/web-beacon-logs.md` must not be overwritten. |

## Non-goals

- Replacing the architecture with a new ingestion system.
- Adding new dependencies without explicit need.
- Turning the core README into an analytics-engineering theory guide.
- Introducing production web-server access logging infrastructure; this plan uses product/access beacon events instead.

## Scope

### In scope
- README reorganization and new curriculum scaffolding.
- Docs alignment.
- Minimal script/dbt/app/report changes needed to support the reordered teaching flow and exact Phase 4 access-log funnel artifacts.
- Verification updates.

### Out of scope
- Large UI redesign.
- New services.
- Warehouse snapshot artifact maintenance unless later approved.

## Success Metrics

- The curriculum order matches the request.
- Learners can inspect every storage boundary with real commands or code-reading checkpoints.
- The README and docs no longer require the learner to infer how DWH/DataLake/app data relate.
- Phase 4 produces a clear, testable access-log enhancement path.


## Contract Enforcement Note

The Phase 4 access-log contract does not require turning `/beacon` into a strict schema gateway. Server validation may remain minimal; generated sample data, dbt tests, and `scripts/verify_pipeline.py` own semantic enforcement.
