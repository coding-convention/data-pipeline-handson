# Deep Interview Spec: Data Pipeline Hands-on Beacon Logs

## Metadata

| Field | Value |
|---|---|
| Profile | Standard |
| Context type | Greenfield / near-empty brownfield |
| Rounds | 6 |
| Final ambiguity | 13% |
| Threshold | 20% |
| Context snapshot | `.omx/context/data-pipeline-hands-on-beacon-logs-20260426T142818Z.md` |
| Transcript | `.omx/interviews/data-pipeline-hands-on-beacon-logs-20260426T144044Z.md` |

## Clarity Breakdown

| Dimension | Score | Notes |
|---|---:|---|
| Intent | 0.90 | Teach the data-engineering blueprint from user behavior logs to usable data. |
| Outcome | 0.90 | Learners can describe and reproduce a local end-to-end log pipeline. |
| Scope | 0.86 | Main README covers data engineering pipeline; analytics engineering is separated into docs. |
| Constraints | 0.80 | Docker Compose, SQLite quiz app, DuckDB, dbt, MinIO, README-first copy/paste progression. |
| Success | 0.80 | Pipeline result is verified through stored logs, transformed tables, and a provided simple visualization. |
| Context | 0.90 | Current repo should scaffold the quiz app and pipeline from scratch. |

## Intent

Create a beginner-friendly data-engineering hands-on lab that helps learners draw the blueprint of “logs becoming data.” The goal is not to memorize DuckDB/dbt/MinIO commands, but to understand enough of the end-to-end flow that they can later find and adapt a method for collecting user behavior or A/B test logs in their own projects.

## Desired Outcome

A learner follows `README.md` from a mostly empty repository and ends with a local pipeline that:

1. Runs all required services with Docker Compose.
2. Serves a very simple quiz web application.
3. Persists quiz questions in SQLite.
4. Emits web beacon logs for user access and quiz interactions.
5. Stores raw beacon logs in MinIO.
6. Loads or queries raw logs with DuckDB.
7. Uses dbt to create simple cleaned/staging/fact-style models.
8. Opens or runs a provided simple visualization/dashboard to confirm the pipeline output.

## In Scope

### Learner-facing main README

- Step-by-step Korean hands-on guide suitable for copy/paste progression.
- Local setup via `docker-compose`.
- A minimal quiz app scaffold in this repository.
- Around 3 seed quiz questions stored in SQLite.
- Beacon logging added to the quiz app.
- Raw log collection and storage pipeline into MinIO.
- DuckDB-based ingestion/querying of raw logs.
- dbt project/models/tests that transform logs into simple usable tables.
- Provided final visualization for verification, not as a full visualization-building lesson.
- Verification commands at each major stage so learners know whether they are on track.

### Beacon event coverage

The main lab should include at least:

- User access / page visit beacon.
- Quiz answer submission event.
- Correct answer result event or field.
- Incorrect answer result event or field.
- Skip/pass/move-to-other-question event.

Implementation may choose the exact JSON schema, but it should be simple enough to read in the README and useful enough to support the final visualization.

### Supporting docs

Create `docs/` reading material for concepts that are useful but outside the core data-engineering hands-on path, especially:

- Difference between data engineering and analytics engineering in this lab.
- Event design basics.
- Metric and A/B test analysis considerations.
- How a future project could extend the simple beacon schema into real product analytics.

## Out of Scope / Non-goals

- UI/UX design polish for the quiz app.
- Production-grade authentication, user management, or deployment.
- A full analytics engineering curriculum inside the main README.
- Having students design dashboards or charts from scratch in the main path.
- Deep metric definition or A/B test statistical analysis in the main path.
- Distributed streaming systems unless explicitly added later.
- Complex orchestration infrastructure beyond what is needed for the hands-on local lab.

## Decision Boundaries

Codex/OMX may decide autonomously, as long as choices support the educational goal:

- Web app language/framework.
- Repository and folder structure.
- Docker Compose service layout.
- Beacon endpoint design.
- Log JSON schema.
- MinIO bucket and object path convention.
- DuckDB database/table names.
- dbt project/model/test names.
- Simple visualization technology.
- Exact README section order and copy/paste exercise structure.

Escalate only if a future choice would materially change the agreed educational scope, introduce significant new dependencies, or move analytics engineering back into the main hands-on path.

## Constraints

- Use DuckDB, dbt, MinIO, and SQLite.
- Use Docker Compose for related services.
- Keep the quiz app intentionally simple: no design emphasis, about 3 questions.
- README should be the primary student path.
- The repo should scaffold the app/pipeline from scratch because current local evidence shows no existing app files.
- Favor clarity, determinism, and copy/paste reliability over production realism.

## Testable Acceptance Criteria

A completed implementation should satisfy:

1. `docker compose up` or documented compose commands start the required local services.
2. The quiz app is accessible locally and shows about 3 quiz questions.
3. Quiz questions persist in SQLite.
4. Visiting the app emits a user/page access beacon.
5. Submitting answers emits logs that preserve answer outcome: correct or incorrect.
6. Skipping/passing to another question emits a log.
7. Raw beacon logs are visible in MinIO with documented bucket/path conventions.
8. DuckDB can read/load the raw logs with documented commands.
9. dbt models run successfully and create cleaned/staging/final tables from the logs.
10. A simple provided visualization can be opened/run and displays data derived from the pipeline.
11. README includes verification checkpoints for the app, MinIO raw logs, DuckDB/dbt output, and visualization.
12. `docs/` includes the separate conceptual reading material for analytics engineering/event design boundaries.

## Assumptions Exposed + Resolutions

- **Assumption:** Students should design event/metric semantics in the main lab.  
  **Resolution:** No. Keep main README focused on data engineering; put analytics engineering guidance in `docs/`.

- **Assumption:** There is an existing app in the repo.  
  **Resolution:** Current repo inspection found no app files, and the user approved scaffolding the quiz app from scratch.

- **Assumption:** Visualization might be a student-built learning task.  
  **Resolution:** No. It is a provided verification/end-state artifact.

## Brownfield Evidence vs Inference Notes

- Evidence: `omx explore` was attempted but failed because the explore harness requires cargo/prebuilt binary.
- Evidence: fallback shell inspection found no source/config files except `.omx/` state/log metadata.
- User-confirmed inference: proceed as greenfield and scaffold the app in this repository.

## Recommended Handoff

Use this spec as the requirements source of truth for planning. Recommended next step:

```bash
$plan --consensus --direct .omx/specs/deep-interview-data-pipeline-hands-on-beacon-logs.md
```

The downstream plan should produce PRD/test-spec artifacts before implementation.
