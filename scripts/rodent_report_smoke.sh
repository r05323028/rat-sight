#!/usr/bin/env bash
set -euo pipefail

# Fixture-only rodent report smoke test. The data is synthetic and no real
# report source is downloaded, read, or imported. Uses an isolated disposable
# PostGIS stack, the production importer/API, and a live Next.js app.
#
# rodent_reports is immutable after import (migration 0004 installs a trigger
# that blocks UPDATE/DELETE). The populated -> empty transition therefore
# recreates the disposable smoke volume instead of deleting rows; the production
# trigger stays installed and no shared developer database is touched.
PROJECT="ratsight-rodent-report-smoke-${BASHPID}"
DB_PORT="55448"
API_PORT="8008"
POSTGRES_DB="ratsight"
POSTGRES_USER="ratsight"
POSTGRES_PASSWORD="ratsight_dev_only"
export POSTGRES_PORT="$DB_PORT" POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
WEB_PORT="3008"
COMPOSE="docker compose -p ${PROJECT} -f infra/docker-compose.yml"
API_PID=""
WEB_PID=""
STACK_STARTED=0
OVERRIDE="$(mktemp)"

kill_tree() {
  local pid="$1"
  local child
  for child in $(pgrep -P "$pid" 2>/dev/null || true); do kill_tree "$child"; done
  kill "$pid" 2>/dev/null || true
}

cleanup() {
  stop_services
  if [[ "$STACK_STARTED" == "1" ]]; then
    $COMPOSE -f "$OVERRIDE" down -v --remove-orphans >/dev/null 2>&1 || true
  fi
  rm -f "$OVERRIDE"
}
trap cleanup EXIT

stop_services() {
  [[ -n "$WEB_PID" ]] && kill_tree "$WEB_PID"
  [[ -n "$API_PID" ]] && kill_tree "$API_PID"
  [[ -n "$WEB_PID" ]] && wait "$WEB_PID" 2>/dev/null || true
  [[ -n "$API_PID" ]] && wait "$API_PID" 2>/dev/null || true
  WEB_PID=""
  API_PID=""
}

start_postgres() {
  $COMPOSE -f "$OVERRIDE" up -d --wait postgres
  export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${DB_PORT}/${POSTGRES_DB}"
}

migrate() {
  uv run --package ratsight-api alembic -c services/api/alembic.ini upgrade head
}

assert_immutability_trigger() {
  local count
  count="$($COMPOSE -f "$OVERRIDE" exec -T postgres \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
    "SELECT count(*) FROM pg_trigger WHERE tgname = 'rodent_reports_immutable'")"
  if [[ "$count" != "1" ]]; then
    echo "error: rodent_reports_immutable trigger is missing after migration" >&2
    exit 1
  fi
}

start_api() {
  uv run --package ratsight-api uvicorn ratsight_api.main:app --host 127.0.0.1 --port "$API_PORT" \
    >"${TMPDIR:-/tmp}/ratsight-rodent-api-smoke.log" 2>&1 &
  API_PID=$!
  for _ in {1..60}; do
    kill -0 "$API_PID" 2>/dev/null || { cat "${TMPDIR:-/tmp}/ratsight-rodent-api-smoke.log" >&2; exit 1; }
    curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1 && break
    sleep 1
  done
  curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null
}

start_web() {
  (
    cd apps/web
    exec env NEXT_PUBLIC_API_URL="http://127.0.0.1:${API_PORT}" NEXT_DIST_DIR=".next-ratsight-rodent-report-smoke" corepack pnpm dev --hostname 127.0.0.1 --port "$WEB_PORT"
  ) >"${TMPDIR:-/tmp}/ratsight-rodent-web-smoke.log" 2>&1 &
  WEB_PID=$!
  for _ in {1..120}; do
    kill -0 "$WEB_PID" 2>/dev/null || { cat "${TMPDIR:-/tmp}/ratsight-rodent-web-smoke.log" >&2; exit 1; }
    curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null 2>&1 && break
    sleep 1
  done
  curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null
}

run_spec() {
  local empty="$1"
  RODENT_SMOKE_EMPTY="$empty" PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" \
    corepack pnpm --filter @ratsight/web exec playwright test e2e/real-rodent-report.spec.ts
}

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  echo "UNVERIFIED/NOT RUN: rodent report smoke unavailable (Docker daemon is unavailable)" >&2
  exit 3
fi
for port in "$DB_PORT" "$API_PORT" "$WEB_PORT"; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "UNVERIFIED/NOT RUN: rodent report smoke unavailable (port ${port} is already occupied)" >&2
    exit 3
  fi
done

cat >"$OVERRIDE" <<YAML
services:
  postgres:
    volumes:
      - ${PROJECT}-postgres-data:/var/lib/postgresql/data
volumes:
  ${PROJECT}-postgres-data:
YAML

export CORS_ORIGINS="http://127.0.0.1:${WEB_PORT},http://localhost:${WEB_PORT}"

# Populated scenario on a fresh disposable volume.
STACK_STARTED=1
start_postgres
migrate
assert_immutability_trigger
uv run python scripts/seed_rodent_report_smoke.py
start_api
start_web
run_spec ""

# Empty scenario: recreate the disposable volume (no DELETE on immutable rows),
# then verify the reset path refuses to clear a non-empty database.
stop_services
$COMPOSE -f "$OVERRIDE" down -v --remove-orphans
start_postgres
migrate
assert_immutability_trigger
SMOKE_EMPTY=1 uv run python scripts/seed_rodent_report_smoke.py
start_api
start_web
run_spec "1"
