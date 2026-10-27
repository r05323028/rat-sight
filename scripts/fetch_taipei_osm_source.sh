#!/usr/bin/env bash
set -euo pipefail

out="${RATSIGHT_OSM_SOURCE:-$HOME/.local/share/ratsight/network/taipei-expanded-ratdar-20261027.osm}"
expected='9db94dd723445fb45e73a77dca4ee4a74783af26e04794fc3fc9d5f63aa0f868'
if [[ ! -f "$out" ]]; then
  echo "error: pinned OSM artifact missing: $out" >&2
  echo "Obtain the approved byte snapshot through the project artifact channel; this script never downloads mutable upstream data." >&2
  exit 1
fi
actual="$(shasum -a 256 "$out" | awk '{print $1}')"
if [[ "$actual" != "$expected" ]]; then
  echo "error: OSM source SHA-256 mismatch (expected $expected, got $actual); existing file was preserved" >&2
  exit 1
fi
echo "verified pinned OSM source: $out"
