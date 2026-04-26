#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
DBT_PROFILES_DIR="${DBT_PROFILES_DIR:-dbt_quiz}"
export DBT_PROFILES_DIR

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
}

require_file "scripts/generate_sample_events.py"
require_file "scripts/upload_logs_to_minio.py"
require_file "scripts/load_minio_to_duckdb.py"
require_file "scripts/render_report.py"
require_file "scripts/verify_pipeline.py"
require_file "dbt_quiz/dbt_project.yml"

if [[ -f "scripts/init_quiz_db.py" ]]; then
  "$PYTHON_BIN" scripts/init_quiz_db.py
fi

if ! find data/raw_spool/beacon_events -name 'events.jsonl' -type f -print -quit 2>/dev/null | grep -q .; then
  "$PYTHON_BIN" scripts/generate_sample_events.py
fi

"$PYTHON_BIN" scripts/upload_logs_to_minio.py
"$PYTHON_BIN" scripts/load_minio_to_duckdb.py
dbt --project-dir dbt_quiz --profiles-dir "$DBT_PROFILES_DIR" run
dbt --project-dir dbt_quiz --profiles-dir "$DBT_PROFILES_DIR" test
"$PYTHON_BIN" scripts/render_report.py
"$PYTHON_BIN" scripts/verify_pipeline.py
