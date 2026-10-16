#!/usr/bin/env bash
set -euo pipefail

# One-time official-source verification. Never used by regular test suites.
PROJECT="ratsight-official-districts-${BASHPID}"
DB_PORT="55440"
API_PORT="8001"
WEB_PORT="3003"
URL="https://data.taipei/api/dataset/1601ef3a-c253-4988-b047-943d9e786143/resource/d8b7eb29-136f-49fc-b14b-3489d3656122/download"
SHA256="77bcc347b503b8ff8a43f7e1afaaedb18877a6222282587b145adaba69afd2d9"
ARCHIVE="$(mktemp -t ratsight-districts.XXXXXX.zip)"
OVERRIDE="$(mktemp)"
API_PID=""
WEB_PID=""
kill_tree() {
  local pid="$1"
  local child
  for child in $(pgrep -P "$pid" 2>/dev/null || true); do kill_tree "$child"; done
  kill "$pid" 2>/dev/null || true
}
COMPOSE="docker compose -p ${PROJECT} -f infra/docker-compose.yml"
cleanup() {
  [[ -n "$WEB_PID" ]] && kill_tree "$WEB_PID"
  [[ -n "$API_PID" ]] && kill_tree "$API_PID"
  [[ -n "$WEB_PID" ]] && wait "$WEB_PID" 2>/dev/null || true
  [[ -n "$API_PID" ]] && wait "$API_PID" 2>/dev/null || true
  $COMPOSE -f "$OVERRIDE" down -v --remove-orphans >/dev/null 2>&1 || true
  rm -f "$ARCHIVE" "$OVERRIDE"
}
trap cleanup EXIT

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  echo "UNVERIFIED/NOT RUN: official district verification unavailable (Docker daemon)" >&2
  exit 3
fi
for port in "$DB_PORT" "$API_PORT" "$WEB_PORT"; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "UNVERIFIED/NOT RUN: official district verification unavailable (port ${port})" >&2
    exit 3
  fi
done

curl -L --fail --max-time 120 -o "$ARCHIVE" "$URL"
actual="$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"
[[ "$actual" == "$SHA256" ]] || { echo "archive SHA-256 mismatch" >&2; exit 1; }

cat >"$OVERRIDE" <<YAML
services:
  postgres:
    volumes:
      - ${PROJECT}-postgres-data:/var/lib/postgresql/data
volumes:
  ${PROJECT}-postgres-data:
YAML
export POSTGRES_PORT="$DB_PORT" POSTGRES_DB=ratsight POSTGRES_USER=ratsight POSTGRES_PASSWORD=ratsight_dev_only
$COMPOSE -f "$OVERRIDE" up -d --wait postgres
export DATABASE_URL="postgresql+psycopg://ratsight:ratsight_dev_only@127.0.0.1:${DB_PORT}/ratsight"
export ADMINISTRATIVE_DISTRICT_DATASET_ID=121199
export CORS_ORIGINS="http://127.0.0.1:${WEB_PORT},http://localhost:${WEB_PORT}"
uv run --package ratsight-api alembic -c services/api/alembic.ini upgrade head
uv run --package ratsight-api python -m ratsight_api.importers.administrative_districts \
  --archive "$ARCHIVE" --archive-sha256 "$SHA256" --source-url "$URL" \
  --dataset-id 121199 --resource-version 20220915 --retrieved-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --license "政府資料開放授權條款-第1版" --attribution "臺北市政府民政局"

uv run --package ratsight-api uvicorn ratsight_api.main:app --host 127.0.0.1 --port "$API_PORT" >/tmp/ratsight-official-api.log 2>&1 & API_PID=$!
for _ in {1..60}; do curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1 && break; sleep 1; done
json="$(curl -fsS "http://127.0.0.1:${API_PORT}/api/v1/administrative-districts")"
python -c 'import json,sys; x=json.loads(sys.argv[1]); assert x["data_state"]=="available"; assert len(x["features"])==12; assert x["provenance"]["dataset_id"]=="121199"' "$json"

(
  cd apps/web
  exec env NEXT_PUBLIC_API_URL="http://127.0.0.1:${API_PORT}" corepack pnpm dev --hostname 127.0.0.1 --port "$WEB_PORT"
) >/tmp/ratsight-official-web.log 2>&1 & WEB_PID=$!
for _ in {1..120}; do curl -fsS "http://127.0.0.1:${WEB_PORT}/" >/dev/null 2>&1 && break; sleep 1; done
PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT="$WEB_PORT" OFFICIAL_DISTRICTS=1 \
  corepack pnpm --filter @ratsight/web exec playwright test e2e/official-district.spec.ts
printf 'OFFICIAL DISTRICT VERIFICATION PASS: hash, 12 unique district features, API, and dashboard path\n'
