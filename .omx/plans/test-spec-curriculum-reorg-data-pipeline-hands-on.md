# Test Spec: Data Pipeline Hands-on Curriculum Reorganization

## Verification Areas

### A. Curriculum structure
| ID | Check | Expected result |
|---|---|---|
| TS-1 | Open `README.md` headings | First four major phases match the requested order |
| TS-2 | Read each phase intro | Each phase states what the learner will learn |
| TS-3 | Read remaining sections | Remaining phases are present and summarized |

### B. Inspection completeness
| ID | Check | Expected result |
|---|---|---|
| TS-4 | Phase 2 DWH subsection | Includes real DuckDB/dbt inspection commands or queries |
| TS-5 | Phase 2 DataLake subsection | Includes raw spool/MinIO inspection tasks |
| TS-6 | Phase 2 app-data subsection | Includes SQLite/app data inspection |
| TS-7 | Phase 2 event-origin subsection | Includes `beacon.js` and `app.py` source checkpoints |

### C. Linkage correctness
| ID | Check | Expected result |
|---|---|---|
| TS-8 | Phase 3 commands | Upload/load/dbt flow matches actual scripts/models |
| TS-9 | Referenced model names | `stg_beacon_events`, `fct_quiz_events`, `mart_quiz_summary` and related marts are spelled correctly |
| TS-10 | Referenced file paths | All paths exist or are intentionally planned touchpoints for implementation |

### D. Access-log extension readiness
| ID | Check | Expected result |
|---|---|---|
| TS-11 | Phase 4 definition | Access-log scope is explicit and consistent with beacon-based event logging |
| TS-12 | Added fields/marts plan | Plan names exact fields (`quiz_step`, `display_order`), exact mart (`mart_access_log_funnel`), exact report section (`접속/문항 노출 퍼널`), and exact verification expectations |
| TS-13 | Verification plan | End-to-end verification covers the deterministic access-log sample sequence → DuckDB columns → dbt staging/fact → `mart_access_log_funnel` → report section |

### E. Docs boundary
| ID | Check | Expected result |
|---|---|---|
| TS-14 | README vs docs | README stays hands-on; extended theory lives in `docs/` |
| TS-15 | `docs/web-beacon-logs.md` | Terminology aligns with access-log teaching |

### F. Safety and merge integrity
| ID | Check | Expected result |
|---|---|---|
| TS-16 | Working tree awareness | Plan explicitly preserves current uncommitted work |
| TS-17 | No dependency creep | Plan does not require new dependencies by default |

## Execution Verification Commands

The eventual implementation should be validated against the existing repository commands, including at minimum:

```bash
docker compose config
docker compose up -d minio createbuckets web
docker compose run --rm pipeline python scripts/init_quiz_db.py
export BOOTSTRAP_DATE=$(date -u +%F)
docker compose run --rm pipeline python scripts/generate_sample_events.py --date "$BOOTSTRAP_DATE" --overwrite
docker compose run --rm pipeline python scripts/upload_logs_to_minio.py
docker compose run --rm pipeline python scripts/load_minio_to_duckdb.py
docker compose run --rm pipeline dbt run --project-dir dbt_quiz --profiles-dir dbt_quiz
docker compose run --rm pipeline dbt test --project-dir dbt_quiz --profiles-dir dbt_quiz
docker compose run --rm pipeline python scripts/render_report.py
docker compose run --rm pipeline python scripts/verify_pipeline.py
```

## Acceptance Gate

The curriculum reorganization is ready for execution only when:

1. The plan explains a single deterministic bootstrap path for Phase 2 inspection without contradicting the actual data flow.
2. The plan gives a concrete and minimal path for Phase 4 access-log enhancements, including exact field names, sample sequence, mart/report artifacts, and verifier assertions.
3. File touchpoints, risks, and verification are explicit enough for an executor lane to act without reopening scope.


## Phase 4 Exact Access-Log Assertions

Implementation must be considered incomplete unless the verifier or equivalent manual checks prove:

- `raw_beacon_events` contains columns `quiz_step` and `display_order`.
- deterministic sample data contains `page_view` rows for `landing`, `question`, and `finish`.
- deterministic sample data contains question-scoped `display_order` values 1, 2, and 3.
- all `answer_submitted` rows have `quiz_step='question'`.
- all `question_skipped` rows have `quiz_step='question'`.
- all `answer_submitted` and `question_skipped` rows have non-null `display_order`.
- deterministic sample answer rows carry display orders 1 and 2, and the deterministic sample skip row carries display order 3.
- dbt creates `mart_access_log_funnel`.
- `mart_access_log_funnel` has columns `quiz_step`, `display_order`, `view_count`, `answer_count`, `skip_count`, `session_count`.
- `reports/quiz_pipeline_report.html` contains the exact section title `접속/문항 노출 퍼널`.

## Phase 2 Bootstrap Ergonomics Assertion

- `BOOTSTRAP_DATE` in the final README should be defined with shell `date -u +%F` or an equivalent Docker-contained command, not host Python.

## Phase 4 Contract Enforcement Boundary

- `/beacon` server validation may remain minimal and event-type focused.
- Phase 4 access-log semantics must be enforced by generated sample data, dbt tests, and `scripts/verify_pipeline.py` assertions.
