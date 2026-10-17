#!/usr/bin/env bash
set -euo pipefail

# Fixture-only rodent report smoke test. The data is synthetic and no real
# report source is downloaded, read, or imported. Uses an isolated disposable
# PostGIS stack, the production importer/API, and a live Next.js app.
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
  [[ -n "$WEB_PID" ]] && kill_tree "$WEB_PID"
  [[ -n "$API_PID" ]] && kill_tree "$API_PID"
  [[ -n "$WEB_PID" ]] && wait "$WEB_PID" 2>/dev/null || true
  [[ -n "$API_PID" ]] && wait "$API_PID" 2>/dev/null || true
  for port in "$WEB_PORT" "$API_PORT"; do
    for pid in $(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true); do kill -9 "$pid" 2>/dev/null || true; done
  done
  if [[ "$STACK_STARTED" == "1" ]]; then
    $COMPOSE -f "$OVERRIDE" down -v --remove-orphans >/dev/null 2>&1 || true
  fi
  rm -f "$OVERRIDE"
}
trap cleanup EXIT

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

STACK_STARTED=1
$COMPOSE -f "$OVERRIDE" up -d --wait postgres
export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${DB_PORT}/${POSTGRES_DB}"
export CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:${WEB_PORT}"
export CORS_ORIGINS="http://127.0.0.1:${WEB_PORT},http://localhost:${WEB_PORT}"
uv run --package ratsight-api alembic -c services/api/alembic.ini upgrade head
uv run python scripts/seed_rodent_report_smoke.py

uv run --package ratsight-api uvicorn ratsight_api.main:app --host 127.0.0.1 --port "$API_PORT" >"${TMPDIR:-/tmp}/ratsight-rodent-api-smoke.log" 2>&1 &
API_PID=$!
for _ in {1..60}; do
  kill -0 "$API_PID" 2>/dev/null || { cat "${TMPDIR:-/tmp}/ratsight-rodent-api-smoke.log" >&2; exit 1; }
  curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null

(
  cd apps/web
  exec env NEXT_PUBLIC_API_URL="http://127.0.0.1:${API_PORT}" corepack pnpm dev --hostname 127.0.0.1 --port "$WEB_PORT"
) >"${TMPDIR:-/tmp}/ratsight-rodent-web-smoke.log" 2>&1 &
WEB_PID=$!
for _ in {1..120}; do
  kill -0 "$WEB_PID" 2>/dev/null || { cat "${TMPDIR:-/tmp}/ratsight-rodent-web-smoke.log" >&2; exit 1; }
  curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null

PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" \
  corepack pnpm --filter @ratsight/web exec playwright test e2e/real-rodent-report.spec.ts

SMOKE_EMPTY=1 uv run python scripts/seed_rodent_report_smoke.py
RODENT_SMOKE_EMPTY=1 PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" \
  corepack pnpm --filter @ratsight/web exec playwright test e2e/real-rodent-report.spec.ts
