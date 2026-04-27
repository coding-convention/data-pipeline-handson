#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
DBT_PROFILES_DIR="${DBT_PROFILES_DIR:-dbt_quiz}"
BOOTSTRAP_DATE="${BOOTSTRAP_DATE:-$(date -u +%F)}"
RESET_SAMPLE_SPOOL="${RESET_SAMPLE_SPOOL:-1}"
CLEAR_RAW_PREFIX="${CLEAR_RAW_PREFIX:-1}"
export DBT_PROFILES_DIR CLEAR_RAW_PREFIX

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

if [[ "$RESET_SAMPLE_SPOOL" == "1" || "$RESET_SAMPLE_SPOOL" == "true" || "$RESET_SAMPLE_SPOOL" == "yes" ]]; then
  rm -rf data/raw_spool/beacon_events
fi

"$PYTHON_BIN" scripts/generate_sample_events.py --date "$BOOTSTRAP_DATE" --overwrite
"$PYTHON_BIN" scripts/upload_logs_to_minio.py
"$PYTHON_BIN" scripts/load_minio_to_duckdb.py
dbt run --project-dir dbt_quiz --profiles-dir "$DBT_PROFILES_DIR"
dbt test --project-dir dbt_quiz --profiles-dir "$DBT_PROFILES_DIR"
"$PYTHON_BIN" scripts/render_report.py
"$PYTHON_BIN" scripts/verify_pipeline.py
