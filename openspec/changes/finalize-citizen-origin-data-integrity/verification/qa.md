# QA record

Session: 2026-10-27, Pi Coding Agent. Machine: macOS-26.3.1-arm64, Python 3.12.3, Next.js 16.4.2.
Network: pinned `taipei-expanded-ratdar-20261027.osm` (71,281 nodes / 208,244 directed edges, sha256 9db94dd7…).
Published snapshot used for the real-data run: dataset `ratdar-taipei-public-export`, resource version `2026-10-26T20:53:32Z`, content sha256 `eae7182b7f1cb57a73c1c074e732a8d5780da0cbdc7c481c3972ec7f3c23c24b`, 91 rows.

## Repository checks

| Command | Result |
| --- | --- |
| `uv run pytest services/api/tests/test_api.py services/api/tests/test_citizen_report_aggregates_api.py services/api/tests/test_simulation_preview.py -q` | 63 passed in 12.31s |
| `make test-py` | 230 passed in 79.51s |
| `make test-js` | 70 passed (3 files) |
| `make typecheck` | 0 errors, 0 warnings, 0 notes |
| `make lint` | All checks passed |
| `make format-check` | 410 files already formatted |
| `make build` | Next.js compiled successfully, 3 static pages |
| `bash scripts/geospatial_smoke.sh` | exit 0 — 14 + 2 + 2 + 2 + 2 + 2 = 24 tests passed (40.5s + 8s), disposable PostGIS, isolated ports 55439/8010/3010 |
| `openspec validate finalize-citizen-origin-data-integrity --strict` | valid |

The committed browser smoke is synthetic-fixture only: it loads `ratsight-smoke-citizen-origin` fixtures into a disposable database. It is not real-data verification.

## Diagnostics and measurements

| Command | Result |
| --- | --- |
| `uv run python scripts/citizen_origin_coverage.py --output docs/benchmarks/citizen-origin-coverage.json` | exit 0 — 91 published / 91 eligible / 91 resolved / 0 zero-candidate; candidates min 3, median 60, p90 107, max 286; histogram 2-4:1, 10-49:34, 50-99:44, 100+:12 |
| `uv run python scripts/benchmark_simulation.py --output docs/benchmarks/citizen-origin-preview.json` | exit 0 — see docs/benchmarks/citizen-origin-preview.json |
| `psql … count(*)` on the published table (read-only) | 91 rows, one resource version, one content digest |

Performance after the reachability change (same machine, snapshot, seed 42): cold load 2,249.7 ms untraced (12,768.7 ms traced upper bound), warm 14.9 ms, graph memory 543.6 MiB peak, candidate resolution median 67.9 ms over 25 cells, reachability 282.7 ms (was 3,597.4 ms), walk 173/229/581 ms at 24/12, 100/30, 500/50, preview 641/674/1,053 ms (was 4,294/4,128/4,500 ms), payload 790,317 / 1,357,782 / 1,769,074 bytes, serialization 8.3/16.4/21.5 ms.

## Real published-snapshot verification (executed)

Read-only against the local developer database container `ratsight-full-local-postgres-1` (127.0.0.1:54330), never modified. No raw records, coordinates, personal text, or image URLs were exported or committed; only aggregate cells were read.

1. FastAPI booted on 127.0.0.1:8011 against that database. `GET /api/v1/citizen-report-aggregates?bbox=121.50,25.00,121.63,25.09` returned 66 published cells with `data_class: CITIZEN_REPORT_AGGREGATE`, `classification: UNVERIFIED`, and full provenance (`dataset_id`, `resource_version`, `content_sha256`, `source_url`, `license`, `attribution`, CRS pair, processing, aggregation).
2. `POST /api/v1/simulations/preview` for `g250m:11137:49031:2026-05:sighting` with the exact `origin_source` returned HTTP 200 in 3.134 s and 1,139,947 bytes: 24 trajectories, 47 in-cell candidates, `uniform-in-cell-v1`, `source_classification: UNVERIFIED`, `source_report_type: sighting`, `source_report_type_eligible: true`, `source_origin_policy_version: origin-report-category-v1`, output `classification: SIMULATED`.
3. A temporary Playwright spec (`apps/web/e2e/tmp-real-snapshot.spec.ts`, since deleted) drove the real Next.js dev server on 127.0.0.1:3011 against the real API and pinned OSM network: 2/2 passed (desktop 7.5 s, mobile 7.4 s). It verified the red marker and card (`公民通報彙整格詳細資料`, UNVERIFIED badge, 鼠蹤通報, report count, resource version), that the request `origin_source` deep-equals the published snapshot identity and `origin_cell_id` equals `cell:month:type`, every provenance field in the response, and playback (`SIMULATED · 起點 …`, 下一步 advancing one step).

Distinction: the committed smoke suite is fixture-only; step 3 above is the real-snapshot browser verification and is reproducible only by re-creating the temporary spec (procedure recorded here) because the spec was removed from the tree.

## OpenSpec quality gate

`make openspec-gate CHANGE=finalize-citizen-origin-data-integrity` → **RESULT: BLOCKED** (expected and honest):

- `[OK]` OpenSpec CLI, gate state, 13 verification runs, code review (PASS_WITH_WARNINGS), engineering traceability (7 requirements), scientific traceability (applicable).
- `[FAIL]` required tasks 15/18 — tasks 16 (scientific approval), 17 (inherited source/privacy/independent review), 18 (gate) remain open by design.
- `[FAIL]` adversarial review BLOCKED by FCO-001, a blocking finding that is not waivable.
- `[FAIL]` human approval required (NEW_SCIENTIFIC_ASSUMPTION) with decision PENDING and no approver/reference recorded.

The change was not archived and no approval was fabricated.

## Not verified

- Scientific validity of the eligibility policy, the 250 m origin cell, or uniform node seeding.
- Written publisher authorization, privacy review, independent review, public-health sign-off.
- Behaviour on hardware other than the recorded machine.
