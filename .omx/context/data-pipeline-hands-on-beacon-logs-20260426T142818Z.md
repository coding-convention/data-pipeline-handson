# Context Snapshot: data-pipeline-hands-on-beacon-logs

- Interview ID: `662c05b8-8355-437e-bd1d-d66c006984d8`
- Created UTC: `20260426T142818Z`
- Profile: Standard
- Context type: greenfield / near-empty brownfield (repository currently has no application/config files discovered)

## Task statement
Data Engineer hands-on learning material: build a web beacon log ingestion pipeline. Students should follow `README.md`, copy/paste code, and evolve the system step-by-step.

## Desired outcome
A Docker Compose based local lab where supporting services are started together and learners implement/extend a simple quiz web app, add web beacon logging, ingest logs, and load/transform/analyze data with the stated stack.

## Stated solution
- Use Docker Compose for related servers.
- Provide README-driven copy/paste implementation steps.
- Simple quiz website with about 3 quiz questions.
- Persist quiz data in SQLite.
- Include web beacon log generation/addition.
- Technology stack: DuckDB, dbt, MinIO.

## Probable intent hypothesis
The user wants a beginner-friendly data-engineering lab that teaches the end-to-end journey from application event generation to object storage/raw ingestion and analytical modeling, without spending effort on UI design.

## Known facts / evidence
- Current working directory: `/Users/ada_l/0hae/03_Side-Projects/data-pipeline-handson`.
- `omx explore` attempted first but failed because cargo/prebuilt explore harness was unavailable.
- Fallback repository inspection found no source/config files at max depth 4 except `.omx/` state/log metadata.
- The user stated the web application is already made, but the local repo evidence does not currently show app files; this may mean the intended app is conceptual, elsewhere, or not yet checked in.

## Constraints
- README must be the primary learner-facing artifact.
- Students should be able to follow by copy/paste.
- Related servers should be started with Docker Compose.
- Keep web app intentionally simple/no design emphasis.
- Stack includes DuckDB, dbt, MinIO, SQLite.

## Unknowns / open questions
- Target learner level and exact learning outcomes.
- Whether the app is truly already present elsewhere or should be scaffolded in this repo.
- Preferred language/framework for the quiz app and beacon endpoint.
- Exact pipeline shape: batch files, object storage layout, streaming/near-real-time, dbt model depth.
- How much code should be prebuilt vs filled in by students.
- Whether MinIO is only raw log storage or also used as pipeline source for DuckDB/dbt.
- Expected validation / grading / final checks.

## Decision-boundary unknowns
- What OMX may decide autonomously (framework, folder structure, event schema, exercise sequence, defaults).
- What must remain fixed by user decision (stack choices, learner level, scope, app framework, deployment assumptions).

## Likely touchpoints
- `README.md`
- `docker-compose.yml`
- Quiz web app source and SQLite seed/migration files
- Beacon endpoint/client script
- MinIO bucket bootstrap scripts
- DuckDB ingestion SQL/scripts
- dbt project/models/tests
- Sample data/log fixtures and verification commands
