#!/usr/bin/env bash
set -euo pipefail

out="${RATSIGHT_OSM_SOURCE:-$HOME/.local/share/ratsight/network/taipei-songshan-20261023.osm}"
expected='faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e'
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
