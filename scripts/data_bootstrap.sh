#!/usr/bin/env bash
set -euo pipefail

# Persistent "full-local" reference-data profile.
#
# Own Compose project + named volume, so the shared `infra` project and its data
# are never touched. Pinned verified sources only; raw archives stay outside Git.
# See openspec/changes/bootstrap-full-local-data and
# docs/infrastructure/full-local-data-bootstrap.md.
PROFILE="${PROFILE:-full-local}"
ACTION="up"
INSPECT_ONLY=0
CITIZEN=0
PURGE=0

for arg in "$@"; do
  case "$arg" in
    up | status | down) ACTION="$arg" ;;
    --inspect-only) INSPECT_ONLY=1 ;;
    --citizen-reports) CITIZEN=1 ;;
    --purge) PURGE=1 ;;
    *)
      echo "error: unknown argument: ${arg}" >&2
      exit 2
      ;;
  esac
done
if [[ "$PROFILE" != "full-local" ]]; then
  echo "error: unsupported profile: ${PROFILE} (supported: full-local)" >&2
  exit 2
fi
if [[ "$PURGE" == "1" && "$ACTION" != "down" ]]; then
  echo "error: --purge is valid only with down" >&2
  exit 2
fi

PROJECT="ratsight-full-local"
DB_PORT="${RATSIGHT_FULL_LOCAL_DB_PORT:-54330}"
POSTGRES_DB="${POSTGRES_DB:-ratsight}"
POSTGRES_USER="${POSTGRES_USER:-ratsight}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-ratsight_dev_only}"
DATA_DIR="${RATSIGHT_FULL_LOCAL_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/ratsight/full-local}"
COMPOSE="docker compose -p ${PROJECT} -f infra/docker-compose.yml -f infra/docker-compose.full-local.yml"

# Pinned verified sources (EVID-TPE-DISTRICT-BOUNDARIES-2026-10-15,
# EVID-TPE-STORMWATER-NETWORK-2026-10-16). Counts are the pinned source records
# only; they do not establish currentness or completeness.
DISTRICTS_FILE="districts-121199-20220915.zip"
DISTRICTS_SHA256="77bcc347b503b8ff8a43f7e1afaaedb18877a6222282587b145adaba69afd2d9"
DISTRICTS_URL="https://data.taipei/api/dataset/1601ef3a-c253-4988-b047-943d9e786143/resource/d8b7eb29-136f-49fc-b14b-3489d3656122/download"
DISTRICTS_EXPECTED=12
STORMWATER_FILE="stormwater-5240223d-2026-02-23.xml"
STORMWATER_SHA256="5d2ea04f7d032d21b07066310e80eb64a34ce8916b4a0c786b10948aeb4e10e4"
STORMWATER_URL="https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=5240223d-5187-454e-b323-63443a195639"
STORMWATER_EXPECTED=19747

DISTRICTS_PATH="${RATSIGHT_DISTRICTS_ARCHIVE:-${DATA_DIR}/${DISTRICTS_FILE}}"
STORMWATER_PATH="${RATSIGHT_STORMWATER_SOURCE:-${DATA_DIR}/${STORMWATER_FILE}}"

# No pinned citizen-report export. Reuse terms for that platform are unverified, so
# the profile never downloads one: point RATSIGHT_CITIZEN_REPORT_SOURCE at a locally
# held export and pass --citizen-reports to publish suppressed 250 m counts only.
CITIZEN_REPORT_PATH="${RATSIGHT_CITIZEN_REPORT_SOURCE:-${DATA_DIR}/citizen-report-export.csv}"
RETRIEVED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Compose interpolation must see these before any `$COMPOSE up`.
export POSTGRES_PORT="$DB_PORT" POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD

import_districts() {
  uv run --package ratsight-api python -m ratsight_api.importers.administrative_districts \
    --archive "$DISTRICTS_PATH" --archive-sha256 "$DISTRICTS_SHA256" \
    --source-url "$DISTRICTS_URL" --dataset-id 121199 --resource-version 20220915 \
    --retrieved-at "$RETRIEVED_AT" --license "政府資料開放授權條款-第1版" \
    --attribution "臺北市政府民政局" "$@"
}

import_stormwater() {
  uv run --package ratsight-api python -m ratsight_api.importers.stormwater_pipelines \
    --source "$STORMWATER_PATH" --archive-sha256 "$STORMWATER_SHA256" \
    --retrieved-at "$RETRIEVED_AT" "$@"
}

import_citizen_reports() {
  uv run --package ratsight-api python -m ratsight_api.importers.citizen_report_aggregates \
    --source "$CITIZEN_REPORT_PATH" "$@"
}

require_citizen_source() {
  [[ -f "$CITIZEN_REPORT_PATH" ]] || {
    echo "error: citizen-report export not found: ${CITIZEN_REPORT_PATH}" >&2
    echo "       --citizen-reports never downloads citizen data; set RATSIGHT_CITIZEN_REPORT_SOURCE" >&2
    exit 2
  }
}

sha_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

fail_before_write() {
  echo "error: $1" >&2
  echo "       no database writes happened: nothing was imported, replaced, or deleted." >&2
  exit 1
}

fail_after_write() {
  echo "error: $1" >&2
  echo "       the two imports commit separately, so this profile is NOT atomic across" >&2
  echo "       layers: whatever finished before this point stays imported. Inspect with" >&2
  echo "       'make data-bootstrap ARGS=status', then rerun to complete the profile." >&2
  exit 1
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo "UNVERIFIED/NOT RUN: full-local bootstrap unavailable (Docker daemon is unavailable)" >&2
    exit 3
  fi
}

project_running() {
  [[ -n "$($COMPOSE ps -q postgres 2>/dev/null)" ]]
}

ensure_source() {
  local path="$1" url="$2" sha="$3"
  if [[ -f "$path" ]]; then
    return 0
  fi
  if [[ "$INSPECT_ONLY" == "1" ]]; then
    echo "error: source not found: ${path}" >&2
    echo "       inspect-only mode never downloads; fetch the pinned source first or drop --inspect-only" >&2
    exit 2
  fi
  mkdir -p "$(dirname "$path")"
  echo "downloading ${url}"
  curl -L --fail --max-time 900 -o "${path}.part" "$url"
  local actual
  actual="$(sha_of "${path}.part")"
  if [[ "$actual" != "$sha" ]]; then
    rm -f "${path}.part"
    fail_before_write "SHA-256 mismatch for ${url} (expected ${sha}, got ${actual}); refusing to import"
  fi
  mv "${path}.part" "$path"
}

verify_sources() {
  verify_one "$DISTRICTS_PATH" "$DISTRICTS_SHA256" "administrative boundaries"
  verify_one "$STORMWATER_PATH" "$STORMWATER_SHA256" "stormwater network"
}

verify_one() {
  local path="$1" sha="$2" label="$3" actual
  [[ -f "$path" ]] || { echo "error: source not found: ${path}" >&2; exit 2; }
  actual="$(sha_of "$path")"
  if [[ "$actual" != "$sha" ]]; then
    fail_before_write "${label} source SHA-256 mismatch for ${path} (expected ${sha}, got ${actual})"
  fi
}

inspect_sources() {
  local districts stormwater
  districts="$(import_districts --inspect-only)"
  stormwater="$(import_stormwater --inspect-only)"
  python3 - "$DISTRICTS_EXPECTED" "$STORMWATER_EXPECTED" "$districts" "$stormwater" <<'PY'
import json, sys

expected_districts, expected_stormwater = int(sys.argv[1]), int(sys.argv[2])
districts, stormwater = json.loads(sys.argv[3]), json.loads(sys.argv[4])
problems = []
if districts["district_count"] != expected_districts:
    problems.append(
        f"administrative boundaries: expected {expected_districts} records, "
        f"folder contains {districts['district_count']}"
    )
if stormwater["record_count"] != expected_stormwater:
    problems.append(
        f"stormwater network: expected {expected_stormwater} records, "
        f"file contains {stormwater['record_count']}"
    )
for problem in problems:
    print(f"error: {problem}", file=sys.stderr)
if problems:
    sys.exit(1)
print(
    f"sources verified: {districts['district_count']} administrative districts "
    f"(SRID {districts['provenance']['target_crs']}), "
    f"{stormwater['record_count']} stormwater records "
    f"(SRID {stormwater['provenance']['target_crs']}, z_handling={stormwater['z_handling']})"
)
PY
}

inventory() {
  $COMPOSE exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F '|' -c "
    select 'administrative_districts', count(*),
           coalesce(min(dataset_id) || '@' || min(resource_version), '-')
      from administrative_districts
    union all
    select 'stormwater_pipelines', count(*),
           coalesce(min(dataset_id) || '@' || min(resource_version), '-')
      from stormwater_pipelines
    order by 1"
  # The aggregate table only exists after migration 0007; older profiles must not
  # fail the inventory, so its row is emitted separately and only when present.
  if [[ "$($COMPOSE exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "select coalesce(to_regclass('public.citizen_report_cells')::text, '')")" == "citizen_report_cells" ]]; then
    $COMPOSE exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F '|' -c "
      select 'citizen_report_cells', count(*),
             coalesce(min(dataset_id) || '@' || min(resource_version), '-')
        from citizen_report_cells"
  fi
}

count_of() {
  $COMPOSE exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "select count(*) from $1"
}

print_next_steps() {
  cat <<TXT

Persisted profile: project ${PROJECT}, volume ${PROJECT}-postgres-data, database port ${DB_PORT}
Sources stay outside Git under ${DATA_DIR}

Start the app tier against this profile (API port 8000, Web port 3080 to avoid the
North/other listeners commonly bound to 3000):
  export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${DB_PORT}/${POSTGRES_DB}"
  uv run --package ratsight-api uvicorn ratsight_api.main:app --host 127.0.0.1 --port 8000
  NEXT_PUBLIC_API_URL="http://127.0.0.1:8000" corepack pnpm --filter @ratsight/web dev --hostname 127.0.0.1 --port 3080

Nothing supervises the app tier: after a daemon restart or reboot, re-run the two
commands above. The database follows Docker's restart policy and the volume persists.

  make data-bootstrap ARGS=status   # counts, provenance, container state
  make data-bootstrap ARGS=down     # stop the profile, keep data
  make data-bootstrap ARGS="down --purge"  # recreate from empty (explicit, destructive)
  make data-bootstrap ARGS="up --citizen-reports"  # needs RATSIGHT_CITIZEN_REPORT_SOURCE

Citizen-report aggregates are CITIZEN_REPORT_AGGREGATE/UNVERIFIED: suppressed 250 m
cell counts with reuse terms still unverified, never observations or a simulation input.

Administrative boundaries are ADMINISTRATIVE_REFERENCE/UNVERIFIED; stormwater is
INFRASTRUCTURE_REFERENCE/UNVERIFIED and publisher-declared reference-only. Counts
describe the pinned source records only: they do not establish currentness,
completeness, connectivity, traversability, rodent movement, risk, or effect.
TXT
}

do_inspect() {
  ensure_source "$DISTRICTS_PATH" "$DISTRICTS_URL" "$DISTRICTS_SHA256"
  ensure_source "$STORMWATER_PATH" "$STORMWATER_URL" "$STORMWATER_SHA256"
  verify_sources
  inspect_sources
  if [[ "$CITIZEN" == "1" ]]; then
    require_citizen_source
    import_citizen_reports --inspect-only
  fi
}

do_up() {
  echo "profile: ${PROFILE} (project ${PROJECT}, database port ${DB_PORT})"
  do_inspect

  require_docker
  if ! project_running; then
    if lsof -nP -iTCP:"$DB_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "error: port ${DB_PORT} is already in use by another process" >&2
      echo "       the bootstrap never stops or reuses unrelated listeners; set" >&2
      echo "       RATSIGHT_FULL_LOCAL_DB_PORT to a free port instead" >&2
      exit 3
    fi
    $COMPOSE up -d --wait postgres
  fi

  export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${DB_PORT}/${POSTGRES_DB}"
  uv run --package ratsight-api alembic -c services/api/alembic.ini upgrade head

  local status=0
  import_districts || status=$?
  if [[ "$status" == "3" ]]; then
    echo "error: administrative boundaries already imported with a different archive hash" >&2
    echo "       keep the existing version or bump --resource-version; the bootstrap never replaces data" >&2
    exit 3
  fi
  if [[ "$status" != "0" ]]; then
    echo "error: administrative district import failed (exit ${status}); nothing was written for stormwater" >&2
    exit "$status"
  fi

  import_stormwater || status=$?
  if [[ "$status" == "3" ]]; then
    echo "error: stormwater network already imported with a different identity or content" >&2
    echo "       keep the existing version or bump --resource-version; the bootstrap never replaces data" >&2
    echo "       administrative boundaries were imported before this point; that layer is unaffected" >&2
    exit 3
  fi
  if [[ "$status" != "0" ]]; then
    echo "error: stormwater import failed (exit ${status})" >&2
    echo "       administrative boundaries were imported before this point; that layer is unaffected" >&2
    exit "$status"
  fi

  if [[ "$CITIZEN" == "1" ]]; then
    require_citizen_source
    echo "note: importing suppressed CITIZEN_REPORT_AGGREGATE counts from ${CITIZEN_REPORT_PATH} ($(sha_of "$CITIZEN_REPORT_PATH"))"
    echo "      counts are UNVERIFIED citizen reports: not observations, not prevalence, not a simulation input"
    import_citizen_reports || {
      echo "error: citizen-report aggregate import failed (exit $?)" >&2
      echo "       administrative and stormwater layers are unaffected" >&2
      exit 1
    }
  fi

  local districts stormwater
  districts="$(count_of administrative_districts)"
  stormwater="$(count_of stormwater_pipelines)"
  [[ "$districts" == "$DISTRICTS_EXPECTED" ]] ||
    fail_after_write "administrative_districts holds ${districts} rows, expected ${DISTRICTS_EXPECTED}"
  [[ "$stormwater" == "$STORMWATER_EXPECTED" ]] ||
    fail_after_write "stormwater_pipelines holds ${stormwater} rows, expected ${STORMWATER_EXPECTED}"

  echo
  echo "inventory (pinned source records; not a completeness claim):"
  inventory | while IFS='|' read -r table rows identity; do
    printf '  %-26s %8s rows  %s\n' "$table" "$rows" "$identity"
  done
  print_next_steps
}

do_status() {
  require_docker
  echo "profile: ${PROFILE} (project ${PROJECT}, database port ${DB_PORT})"
  if ! project_running; then
    echo "status: database not running (run: make data-bootstrap)"
    exit 0
  fi
  $COMPOSE ps postgres
  local schema_table
  if ! schema_table="$($COMPOSE exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "select to_regclass('public.administrative_districts')")"; then
    echo "error: could not inspect the profile database schema" >&2
    exit 1
  fi
  if [[ "$schema_table" != "administrative_districts" ]]; then
    echo "status: database is not migrated (run: make data-bootstrap)"
    exit 0
  fi
  echo
  echo "inventory (pinned source records; not a completeness claim):"
  inventory | while IFS='|' read -r table rows identity; do
    printf '  %-26s %8s rows  %s\n' "$table" "$rows" "$identity"
  done
  echo
  echo "sources under ${DATA_DIR}:"
  for path in "$DISTRICTS_PATH" "$STORMWATER_PATH"; do
    if [[ -f "$path" ]]; then
      printf '  %s  %s\n' "$(sha_of "$path")" "$path"
    else
      printf '  %s  (missing)\n' "$path"
    fi
  done
}

do_down() {
  require_docker
  if [[ "$PURGE" == "1" ]]; then
    echo "purging ${PROJECT}: stopping containers and deleting volume ${PROJECT}-postgres-data"
    $COMPOSE down -v --remove-orphans
    echo "recreate with: make data-bootstrap"
  else
    echo "stopping ${PROJECT}; data in ${PROJECT}-postgres-data is preserved"
    $COMPOSE down --remove-orphans
    echo "recreate with: make data-bootstrap (existing rows are reused, not re-imported)"
  fi
}

case "$ACTION" in
  up)
    if [[ "$INSPECT_ONLY" == "1" ]]; then
      echo "profile: ${PROFILE} (inspect-only: no database writes, no volume changes)"
      do_inspect
      echo "inspect-only: checks passed; nothing was written"
    else
      do_up
    fi
    ;;
  status) do_status ;;
  down) do_down ;;
esac
