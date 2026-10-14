#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RIG_FILE="${RIG_FILE:-$ROOT_DIR/rig.yaml}"
PI_AGENT_HOME="${PI_AGENT_HOME:-$HOME/.pi/agent}"
OPENRIG_HOME="${OPENRIG_HOME:-$HOME/.openrig}"
MODE="dry-run"
RESOURCES=(models.json)

usage() {
  cat <<'HELP'
Usage: scripts/setup-pi-seats.sh [--dry-run|--apply] [--auth] [--mcp] [--extensions]

Default: dry-run and link models.json only. --apply creates each isolated
OpenRig Pi seat agent directory and symlinks selected resources. Authentication,
MCP configuration, and extensions require explicit opt-in. settings.json is
never linked. Existing destinations are never overwritten.
HELP
}

while (($#)); do
  case "$1" in
    --dry-run) MODE="dry-run" ;;
    --apply) MODE="apply" ;;
    --models) ;;
    --auth) RESOURCES+=(auth.json) ;;
    --mcp) RESOURCES+=(mcp.json) ;;
    --extensions) RESOURCES+=(extensions) ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if ! command -v rig >/dev/null 2>&1; then
  echo "OpenRig CLI 'rig' required to validate the RigSpec." >&2
  exit 2
fi
if ! rig spec validate --json "$RIG_FILE" >/dev/null; then
  echo "RigSpec validation failed: $RIG_FILE" >&2
  exit 1
fi

OPENRIG_HOME="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).expanduser().resolve())' "$OPENRIG_HOME")"
PI_AGENT_HOME="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).expanduser().resolve())' "$PI_AGENT_HOME")"

# RigSpec YAML is validated above; parse its stable pod/member id indentation.
SEATS=()
while IFS= read -r row; do
  SEATS+=("$row")
done < <(python3 - "$RIG_FILE" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
name_match = re.search(r"^name:\s*[\"']?([^\"'\s]+)", text, re.MULTILINE)
if not name_match:
    raise SystemExit("RigSpec has no top-level name")
rig_name = name_match.group(1)
pod = None
seats = []
in_pods = False
for line in text.splitlines():
    if line == "pods:":
        in_pods = True
        continue
    if in_pods and line and not line.startswith(" "):
        break
    pod_match = re.match(r"^  - id:\s*([A-Za-z0-9_-]+)\s*$", line)
    if pod_match:
        pod = pod_match.group(1)
        continue
    member_match = re.match(r"^      - id:\s*([A-Za-z0-9_-]+)\s*$", line)
    if in_pods and pod and member_match:
        seats.append((pod, member_match.group(1)))
if not seats:
    raise SystemExit("RigSpec contains no pod members")
for pod_id, member_id in seats:
    print(f"{rig_name}\t{pod_id}\t{member_id}")
PY
)

if ((${#SEATS[@]} == 0)); then
  echo "Could not derive OpenRig seats from $RIG_FILE" >&2
  exit 1
fi

ERRORS=0
LINK_COUNT=0
for row in "${SEATS[@]}"; do
  IFS=$'\t' read -r rig_name pod_id member_id <<< "$row"
  session="${pod_id}-${member_id}@${rig_name}"
  seat_agent="$OPENRIG_HOME/state/pi/$session/agent"
  printf 'Seat %s -> %s\n' "$session" "$seat_agent"
  if [[ "$MODE" == "apply" ]]; then
    if [[ -L "$seat_agent" || ( -e "$seat_agent" && ! -d "$seat_agent" ) ]]; then
      printf 'Refusing unexpected seat path: %s\n' "$seat_agent" >&2
      ERRORS=$((ERRORS + 1))
      continue
    fi
    mkdir -p "$seat_agent"
  fi
  for resource in "${RESOURCES[@]}"; do
    source="$PI_AGENT_HOME/$resource"
    target="$seat_agent/$resource"
    if [[ ! -e "$source" ]]; then
      printf 'Skip missing source: %s\n' "$source"
      continue
    fi
    if [[ -L "$target" ]]; then
      existing="$(readlink "$target")"
      if [[ "$existing" == "$source" ]]; then
        printf 'Validated existing link: %s -> %s\n' "$target" "$source"
        LINK_COUNT=$((LINK_COUNT + 1))
      else
        printf 'Refusing to replace existing link: %s -> %s\n' "$target" "$existing" >&2
        ERRORS=$((ERRORS + 1))
      fi
    elif [[ -e "$target" ]]; then
      printf 'Refusing to replace existing path: %s\n' "$target" >&2
      ERRORS=$((ERRORS + 1))
    elif [[ "$MODE" == "dry-run" ]]; then
      printf 'Would link: %s -> %s\n' "$target" "$source"
    else
      ln -s "$source" "$target"
      if [[ -L "$target" && "$(readlink "$target")" == "$source" ]]; then
        printf 'Created and validated: %s -> %s\n' "$target" "$source"
        LINK_COUNT=$((LINK_COUNT + 1))
      else
        printf 'Symlink validation failed: %s\n' "$target" >&2
        ERRORS=$((ERRORS + 1))
      fi
    fi
  done
done

printf 'Mode: %s; seats: %s; validated/existing links: %s; errors: %s\n' "$MODE" "${#SEATS[@]}" "$LINK_COUNT" "$ERRORS"
((ERRORS == 0))
