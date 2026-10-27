#!/usr/bin/env bash
set -euo pipefail

# Real browser-to-FastAPI smoke test. The fixture is synthetic test data only.
PROJECT="ratsight-geospatial-smoke-${BASHPID}"
DB_PORT="55439"
API_PORT="8010"
POSTGRES_DB="ratsight"
POSTGRES_USER="ratsight"
POSTGRES_PASSWORD="ratsight_dev_only"
export POSTGRES_PORT="$DB_PORT" POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
WEB_PORT="3010"
export CORS_ORIGINS="http://127.0.0.1:${WEB_PORT},http://localhost:${WEB_PORT}"
COMPOSE="docker compose -p ${PROJECT} -f infra/docker-compose.yml"
API_PID=""
WEB_PID=""
STACK_STARTED=0
OVERRIDE="$(mktemp)"
TSCONFIG="apps/web/tsconfig.json"
TSCONFIG_BACKUP="$(mktemp)"
TSCONFIG_SAVED=0
NEXT_ENV="apps/web/next-env.d.ts"
NEXT_ENV_BACKUP="$(mktemp)"
NEXT_ENV_SAVED=0
NEXT_DIST_DIR=".next-ratsight-smoke-${BASHPID}"
export RATSIGHT_ENABLE_SYNTHETIC_AGGREGATE_FIXTURE=1
export RATSIGHT_CITIZEN_REPORT_DATASET_ID="ratsight-smoke-citizen-origin"
export RATSIGHT_OSM_SOURCE="${RATSIGHT_OSM_SOURCE:-$HOME/.local/share/ratsight/network/taipei-expanded-ratdar-20261027.osm}"
kill_tree() {
  local pid="$1"
  local child
  for child in $(pgrep -P "$pid" 2>/dev/null || true); do kill_tree "$child"; done
  kill "$pid" 2>/dev/null || true
}
cleanup() {
  [[ -n "$WEB_PID" ]] && kill_tree "$WEB_PID"
  [[ -n "$API_PID" ]] && kill_tree "$API_PID"
  [[ -n "$WEB_PID" ]] && wait "$WEB_PID" 2>/dev/null || true
  [[ -n "$API_PID" ]] && wait "$API_PID" 2>/dev/null || true
  if [[ "$STACK_STARTED" == "1" ]]; then
    $COMPOSE -f "$OVERRIDE" down -v --remove-orphans >/dev/null 2>&1 || true
  fi
  if [[ "$TSCONFIG_SAVED" == "1" ]]; then
    cp "$TSCONFIG_BACKUP" "$TSCONFIG"
  fi
  if [[ "$NEXT_ENV_SAVED" == "1" ]]; then
    cp "$NEXT_ENV_BACKUP" "$NEXT_ENV"
  fi
  rm -f "$OVERRIDE" "$TSCONFIG_BACKUP" "$NEXT_ENV_BACKUP"
  rm -rf "apps/web/${NEXT_DIST_DIR}"
}
trap cleanup EXIT

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  echo "UNVERIFIED/NOT RUN: geospatial smoke unavailable (Docker daemon is unavailable)" >&2
  exit 3
fi
if [[ ! -f "$RATSIGHT_OSM_SOURCE" ]]; then
  echo "UNVERIFIED/NOT RUN: geospatial smoke unavailable (pinned OSM source is absent: $RATSIGHT_OSM_SOURCE)" >&2
  exit 3
fi
for port in "$DB_PORT" "$API_PORT" "$WEB_PORT"; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "UNVERIFIED/NOT RUN: geospatial smoke unavailable (port ${port} is already occupied)" >&2
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

STACK_STARTED=1
$COMPOSE -f "$OVERRIDE" up -d --wait postgres
export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${DB_PORT}/${POSTGRES_DB}"
export ADMINISTRATIVE_DISTRICT_DATASET_ID="smoke-fixture"
export STORMWATER_DATASET_ID="00000000-0000-4000-8000-000000000001"
uv run --package ratsight-api alembic -c services/api/alembic.ini upgrade head
uv run python scripts/seed_geospatial_smoke.py
uv run python scripts/seed_stormwater_smoke.py
uv run python scripts/seed_citizen_report_smoke.py

uv run --package ratsight-api uvicorn ratsight_api.main:app --host 127.0.0.1 --port "$API_PORT" >"${TMPDIR:-/tmp}/ratsight-api-smoke.log" 2>&1 &
API_PID=$!
for _ in {1..60}; do
  kill -0 "$API_PID" 2>/dev/null || { cat "${TMPDIR:-/tmp}/ratsight-api-smoke.log" >&2; exit 1; }
  curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null

# Next dev rewrites tsconfig.json and next-env.d.ts for each unique distDir.
# Restore the exact pre-smoke files in cleanup so the isolated build cannot
# dirty tracked config.
cp "$TSCONFIG" "$TSCONFIG_BACKUP"
TSCONFIG_SAVED=1
cp "$NEXT_ENV" "$NEXT_ENV_BACKUP"
NEXT_ENV_SAVED=1
(
  cd apps/web
  exec env NEXT_PUBLIC_API_URL="http://127.0.0.1:${API_PORT}" NEXT_DIST_DIR="$NEXT_DIST_DIR" corepack pnpm dev --hostname 127.0.0.1 --port "$WEB_PORT"
) >"${TMPDIR:-/tmp}/ratsight-web-smoke.log" 2>&1 &
WEB_PID=$!
for _ in {1..120}; do
  kill -0 "$WEB_PID" 2>/dev/null || { cat "${TMPDIR:-/tmp}/ratsight-web-smoke.log" >&2; exit 1; }
  curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null

PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" corepack pnpm --filter @ratsight/web exec playwright test e2e/real-citizen-origin.spec.ts
SMOKE_EMPTY=1 uv run python scripts/seed_citizen_report_smoke.py
PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" corepack pnpm --filter @ratsight/web exec playwright test e2e/real-citizen-origin-empty.spec.ts
PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" corepack pnpm --filter @ratsight/web exec playwright test e2e/real-api.spec.ts
SMOKE_EMPTY=1 uv run python scripts/seed_geospatial_smoke.py
PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" corepack pnpm --filter @ratsight/web exec playwright test e2e/real-api-empty.spec.ts
PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" corepack pnpm --filter @ratsight/web exec playwright test e2e/real-stormwater.spec.ts
SMOKE_EMPTY=1 uv run python scripts/seed_stormwater_smoke.py
PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" corepack pnpm --filter @ratsight/web exec playwright test e2e/real-stormwater-empty.spec.ts
