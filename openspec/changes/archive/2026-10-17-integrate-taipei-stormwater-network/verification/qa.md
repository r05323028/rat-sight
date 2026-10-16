# Independent QA — integrate-taipei-stormwater-network

**Verdict: CLEAR** for the requested QA scope, with one material limitation recorded below.

- Qitem: `qitem-20261016173129-f90dbd5dc5e49457`
- Evaluator: `verification.qa@rat-team` (not an author of the implementation)
- Candidate: uncommitted diff `openspec/changes/integrate-taipei-stormwater-network` on `main` at `13f2390`
- Date: 2026-10-16
- Scope: independent, read-only. No implementation file edited.

## User outcome checked

A user can import the documented Taipei stormwater resource and inspect it as an
`INFRASTRUCTURE_REFERENCE` / `UNVERIFIED` line layer with bounded viewport queries, typed
provenance, and no inferred connectivity, while administrative and synthetic layers stay
independent.

## Commands and results

Environment: macOS, Python 3.12 (uv), Node 26 (pnpm), Docker 29.7.2,
`ghcr.io/baosystems/postgis:17-3.5`.

| # | Command | Result |
|---|---------|--------|
| V1 | `openspec validate integrate-taipei-stormwater-network` | **valid**; 3 long-requirement warnings |
| V2 | `uv run pytest -q` | **117 passed** |
| V3 | `uv run pytest services/api/tests/test_stormwater_pipelines_import.py services/api/tests/test_stormwater_pipelines_api.py -q` | **36 passed** |
| V4 | `corepack pnpm --filter @ratsight/web test` | **3 files / 28 tests passed** |
| V5 | `corepack pnpm --filter @ratsight/web typecheck` | **pass** |
| V6 | `corepack pnpm --filter @ratsight/web lint` | **pass** |
| V7 | `corepack pnpm --filter @ratsight/web format:check` | **pass** (Prettier clean) |
| V8 | `corepack pnpm --filter @ratsight/web build` | **pass** |
| V9 | `corepack pnpm --filter @ratsight/web e2e` (default) | **4 passed, 5 skipped** (real-API + official specs skip by design) |
| V10 | `make geospatial-smoke` | **4 real-API specs passed**: admin available, admin empty, stormwater available, stormwater empty |
| V11 | `bash scripts/verify_official_districts.sh` | **PASS** — see below |
| V12 | `uv run basedpyright` | **0 errors, 0 warnings, 0 notes** |
| V13 | `uv run ruff check <feature files>` + `ruff format --check <feature files>` + `bash -n` both scripts | **pass** |
| V14 | `make openspec-gate CHANGE=integrate-taipei-stormwater-network` | **PASS** — reviews, QA evidence, and five requirement mappings recorded |

### Real smoke detail (V10)

`make geospatial-smoke` boots an isolated `ratsight-geospatial-smoke-<pid>` stack on
DB 55439 / API 8000 / web 3002, migrates `0001→0003`, seeds the administrative and
stormwater fixtures through production validation/provenance/persistence functions, and runs
both layers' available and empty specs. Only the external basemap style is mocked; no
application API route is intercepted. Post-run: **no listeners on 3002/8000/55439**, **no
smoke containers or volumes**, dev `infra-postgres-1` and `infra_ratsight-postgres-data`
untouched.

### Official district verification (V11)

`scripts/verify_official_districts.sh` downloaded the documented official archive,
matched SHA-256 `77bcc347…d2d9`, applied migrations in a disposable
`ratsight-official-districts-<pid>` stack (DB 55440 / API 8001 / web 3003), imported **12**
districts, asserted the live API returned `data_state=available`, 12 features, and
`provenance.dataset_id=121199`, and passed `official-district.spec.ts`. Post-run: **no
listeners on 3003/8001/55440**, **no official containers/volumes**, **no leftover temp
archive**; dev PostGIS untouched.

### PostGIS isolation / cleanup

Both harnesses use per-run isolated compose projects and disposable named volumes, fail
closed on occupied ports, and run `down -v --remove-orphans` on their own project only. The
shared dev container/volume were confirmed present and unchanged after both runs.

## Contract, provenance, classification, and no-topology checks

- **Classification separation:** `StormwaterProperties.data_class` is the literal
  `INFRASTRUCTURE_REFERENCE` and `classification` is the literal `UNVERIFIED`; the
  `stormwater_pipelines` table CHECKs enforce `data_class='INFRASTRUCTURE_REFERENCE'` and the
  epistemic vocabulary. `INFRASTRUCTURE_REFERENCE` is not an epistemic `Classification`
  value.
- **Typed provenance:** `StormwaterProvenanceV1` (`extra="forbid"`) has exactly
  `schema_version, source_url, download_url, dataset_id, resource_id, resource_version,
  retrieved_at, archive_sha256, license, attribution, source_crs, target_crs, z_handling,
  processing, source_quality, uncertainty`; URLs are http(s), IDs are UUIDs, timestamps
  RFC3339 UTC `Z`, hash is 64 lowercase hex. `z_handling="dropped"` for this resource.
- **Feature allowlist:** `segment_id` + the 19 nullable source attributes + the required
  provenance references (`provenance_schema_version`, `dataset_id`, `resource_version`,
  `archive_sha256`) + `data_class` + `classification`; persistence-only `source_record_id`
  is not exposed as a separate property. UI renders missing values as `Unavailable`.
- **Bbox contract:** `parse_bbox` requires exactly four finite numbers, longitude/latitude
  ranges, `min≤max`, and width/height ≤ 0.30°; violations return HTTP 422. The dashboard
  short-circuits an over-broad viewport and queries the map viewport on load and debounced
  `moveend`.
- **Empty vs miss vs failure:** storage-empty returns 200 `data_state=empty`; an in-view miss
  returns `available` with `feature_count=0`; storage failure is 503 and invalid persisted
  data is 500 — never fallback geometry. Cap is 5,000 with `truncated=true`.
- **No topology:** endpoint IDs (`start_node_id`/`end_node_id`) and `pipe_number` are stored
  and exposed only as nullable publisher attributes; the importer does not build a graph,
  merge rows, or infer connectivity, and duplicates/missing values are counted in
  `source_quality` without repair.
- **Importer integrity:** the CLI pins the Candidate B dataset/resource/version/hash unless
  the explicit test-only `--allow-nonofficial-source` flag is passed; re-import with a
  different hash or changed/omitted record set fails closed.
- **Simulation integrity:** `MapView` filters synthetic edges to `visits > 0`, covered by
  `does not render unvisited synthetic edges`.
- **Layer independence:** administrative, stormwater, and simulation sources/layers have
  distinct source IDs, separate visibility state, and separate stale-layer removal.

## Material limitation

- The **official Candidate B stormwater archive was not imported** in this pass: the bytes
  are not committed and there is no official-stormwater verification script (the one-time
  official check covers administrative districts only). The stormwater importer/API were
  exercised with a deterministic synthetic fixture and the importer's official identity/hash
  are pinned, but real-source parsing/geometry of the 19,747-record archive remains
  **UNVERIFIED**. This matches the evidence-record limitation and should be stated in
  acceptance language.

## Other limitations

- Live bbox **miss/truncation** UI states were verified by source inspection and unit tests,
  not by a live e2e exercising a real miss or a >5,000 cap.
- The OpenSpec quality gate now passes; its recorded references and judgments are not authenticated by the gate itself.
- Standing repo-hygiene item (outside this change): untracked `.agents/skills/sem/**` +
  `skills-lock.json` still break repo-wide `ruff check .` (13 E501) and
  `ruff format --check .` (4 files); feature files are clean.

## QA position

All requested checks pass and the isolated official district verification succeeded. The one
material evidence gap is the unexercised official stormwater source import; the lead should
weigh that before acceptance. No functional defect was found in the requested scope.
