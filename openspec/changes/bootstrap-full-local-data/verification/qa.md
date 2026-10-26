# QA verification — bootstrap-full-local-data

Independent QA run by `verification.qa` (rat-team) on 2026-10-23, in the working tree at
`d6bcb40`-based state with the in-flight `localize-web-traditional-chinese` changes present.
Every row below was executed by the verifier; raw transcripts are in `/tmp/qa-full-local/`.
An unlisted behaviour is not verified.

Scope: the persistent `full-local` profile, its lifecycle commands, the pinned-source
fail-closed behaviour, the optional synthetic fixture, and the populated dashboard read path.
Not claimed: currentness, completeness, connectivity, or traversability of any source; any
rodent observation, movement, or risk; municipal acceptance; scientific review.

## Isolation and ownership

| Item | Value |
| --- | --- |
| Compose project | `ratsight-full-local` (`infra/docker-compose.full-local.yml`) |
| Owned volume | `ratsight-full-local_ratsight-full-local-postgres-data` |
| Profile DB port | `127.0.0.1:54330` |
| App tier used for this run | API `127.0.0.1:8001`, Web `127.0.0.1:3081` (`DATABASE_URL` → 54330) |
| Shared infra | `infra-postgres-1` on `127.0.0.1:54329`, volume `infra_ratsight-postgres-data` (created 2026-10-15T16:34:38Z) |
| Untouched occupants | `127.0.0.1:8000` (foreign `uvicorn --reload`, pid 16716, `/health` 200 through the whole run), `127.0.0.1:3000` (unrelated node process) |

Shared-DB baseline at start: `administrative_districts` 0, `stormwater_pipelines` 0,
`rodent_reports` 5. End state after the run: shared container `Up 41 hours (healthy)`, shared
volume `CreatedAt` unchanged `2026-10-15T16:34:38Z` — nothing in `infra` was written to.

## Lifecycle, inventory and fail-closed behaviour

| ID | Command | Exit | Observed |
| --- | --- | --- | --- |
| V-STATUS | `make data-bootstrap ARGS=status` | 0 | `12 rows 121199@20220915` / `5 rows 00000000-0000-4000-8000-000000000002@2026-10-17T00:00:00Z` (after the synthetic step) / `19747 rows 97b82d58-faba-4ee4-9488-dd5d04a79efd@2026-02-23T17:10:41Z`; both archive SHA-256 printed; container `Up (healthy)` |
| V-UP | `make data-bootstrap ARGS=up` | 0 | 171 s. `sources verified: 12 administrative districts (SRID EPSG:4326), 19747 stormwater records (SRID EPSG:4326, z_handling=dropped)`; `"inserted": 12`, `"inserted": 19747`; `rodent_reports is empty: synthetic fixtures stay opt-in (pass --synthetic)` |
| V-RERUN | `make data-bootstrap ARGS=up` (second run) | 0 | 136 s. `"inserted": 0, "unchanged": 12` and `"inserted": 0, "unchanged": 19747`. `max(updated_at)` did not move, so the rerun writes nothing — no provenance rewrite |
| V-MISMATCH | `RATSIGHT_DISTRICTS_ARCHIVE=/tmp/qa-full-local/bad-districts.zip make data-bootstrap ARGS=up` | 2 (script 1) | `error: administrative boundaries source SHA-256 mismatch for /tmp/qa-full-local/bad-districts.zip (expected 77bcc347…, got a5320f3b…)` then `no database writes happened: nothing was imported, replaced, or deleted.` |
| V-SECOND | valid districts archive + corrupted stormwater archive, `ARG` as above | 1 | Same fail-closed shape. Canary `max(updated_at)` admin `2026-10-23 07:58:32.700422+00` and stormwater `2026-10-23 07:59:47.272419+00` unchanged after V-MISMATCH and V-SECOND, so the second-source check also runs before any write |
| V-INSPECT | `RATSIGHT_DISTRICTS_ARCHIVE=/tmp/qa-full-local/missing.zip make data-bootstrap ARGS="up --inspect-only"` | 2 | `error: source not found: /tmp/qa-full-local/missing.zip`, `inspect-only mode never downloads` |
| V-PURGREJECT | `make data-bootstrap ARGS="status --purge"` | 2 | `error: --purge is valid only with down` |
| V-PURGE | `make data-bootstrap ARGS="down --purge"` | 0 | `Container ratsight-full-local-postgres-1 Removed`, `Volume ratsight-full-local_ratsight-full-local-postgres-data Removed`, `Network ratsight-full-local_default Removed`, `recreate with: make data-bootstrap`. `docker ps -a` / `docker volume ls` for the project then empty |
| V-RECREATE | `make data-bootstrap ARGS=status` then `ARGS=up` | 0 / 0 | status: `database not running (run: make data-bootstrap)`. up: 171 s, `inserted 12` + `inserted 19747`, volume `ratsight-full-local_ratsight-full-local-postgres-data` present again, rows `12/19747/0` (rodent stayed opt-in) |

## Restart persistence (V-RESTART)

Killed the API process on 8001 and the Web process on 3081, restarted both against the same
profile, and re-read the data.

- API `/health` → 200 within the wait loop; process id changed.
- `/api/v1/administrative-districts` → `available`, 12 features, `dataset_id` 121199.
- `/api/v1/stormwater-pipelines?bbox=121.50,25.00,121.60,25.06` → 5000 features, `feature_count`
  5000, `truncated` true.
- Web `GET /` → 200.
- Row counts after both restarts: `12/19747/0` — unchanged, no re-import needed.

This is the API/Web restart row that `tasks.md` task 10 previously listed as remaining. A Docker
daemon restart or host reboot is **not** covered here: per the lead's decision the app tier is
re-launched by the operator while PostGIS data persists, so that path is documented, not automated.

## API and populated dashboard

| ID | Check | Observed |
| --- | --- | --- |
| V-API | `/api/v1/administrative-districts` | `data_state` `available`, 12 features; provenance carries `source_url`, `retrieved_at`, `archive_sha256`, `license 政府資料開放授權條款-第1版`, `attribution 臺北市政府民政局`, `source_crs EPSG:3826` → `target_crs EPSG:4326`, 12 Polygon/MultiPolygon, `uncertainty.currentness "resource version 20220915; legal currency after this version is unresolved"` |
| V-API | `/api/v1/stormwater-pipelines?bbox=121.50,25.00,121.60,25.06` | 5000 features, `truncated` true, bounded response |
| V-API | `/api/v1/stormwater-pipelines?bbox=120.0,24.0,122.5,25.5` | HTTP 422 `{"detail":"bbox width and height must not exceed 0.3 degrees"}` |
| V-BROWSER | headless Chromium (playwright 1.64.1) against `http://127.0.0.1:3081` | Title `見光鼠 RatSight · 都市鼠類移動分析` (the in-flight localization is live). `panel-count` 9. Three layer checkboxes at rest (行政區 / 雨水下水道管線 / 鼠類回報), four after a preview. All 12 districts listed (松山 信義 大安 中山 中正 大同 萬華 文山 南港 內湖 士林 北投). District selection panel: `行政區 松山區`, `行政區 ID 63001`, `資料類別 ADMINISTRATIVE_REFERENCE`, `分類 UNVERIFIED · 未驗證`, `資料集 121199`, `資源版本 20220915` |
| V-BROWSER | stormwater panel at default view | `僅顯示部分資料 · 請放大`; `目前視窗範圍內回傳 5000 條管線。 已達回傳上限：除這些回傳圖徵外仍有符合條件的管線，且不宣稱精確總數。`; list notice `僅顯示前 100 條管線；其他圖徵請直接在地圖上選取。`; provenance includes `來源品質 缺少管號： 20 · 重複管號值： 310 · 缺少起點： 992 · 缺少終點： 991 · 缺少備註： 17950`, `垂直坐標 來源 Z 已捨棄 — 無文件化的垂直坐標參考系統`, `未驗證實際連通性。起點／終點節點值僅為發布機關屬性。` |
| V-BROWSER | pan (slow drag) | One new bounded request `bbox=121.48881,24.94906,121.71968,25.08171` (0.23087° × 0.13265°, inside the 0.3° cap) — the dashboard re-queries on pan instead of reusing the initial window |
| V-BROWSER | zoom out past the cap | 0 extra stormwater requests, row copy `請放大以載入管線` — the guard is client-side, so no 422 spam |
| V-BROWSER2 | recheck after the lead's context-line fix, same runtime | default `底圖 · 參考邊界 · 雨水下水道參考資料 · 無鼠類觀測資料`; zoomed out `底圖 · 參考邊界 · 雨水下水道請放大載入 · 無鼠類觀測資料`; the string `無雨水下水道資料` is absent from the DOM while 19,747 rows exist; panel copy `請放大以載入管線。目前視圖超過載入上限，因此清單暫不顯示，並不代表沒有資料。`; zoom actions issued 0 requests |
| V-BROWSER2 | pipeline detail (previously ambiguous probe, retried) | Selecting the first list entry produced `管段 ID AE`, `類別代碼 8040201`, `管號 4752-p3-p4`, `起點節點（發布機關屬性） 4752-p3`, `終點節點（發布機關屬性） 4752-p4`, `管理單位 AE`, `尺寸單位 3`, `直徑／寬 0.4`, `直徑／高 1.02`, `管孔數 1`, `材質 FRP`, `長度 5.108`, `資料類別 INFRASTRUCTURE_REFERENCE`, `分類 UNVERIFIED · 未驗證` |

Zero console errors in every browser probe.

Screenshots: `p1-initial.png`, `p2-district.png`, `p2-pipeline.png`, `p2-panned.png`,
`p2-zoomed-out.png`, `p2-preview.png`, `p3-pan.png`, `p4-pipeline-selected.png`,
`p4-zoomed-out.png`, `p5-synthetic-rodent.png` — all under `/tmp/qa-full-local/`.

## Optional synthetic demo

| ID | Check | Observed |
| --- | --- | --- |
| V-SYNTH | `make data-bootstrap ARGS="up --synthetic"` | 0, 136 s. `note: importing the committed SYNTHETIC rodent fixture (opt-in; SIMULATED, not observed)`; `"inserted": 5` for rodent while admin/stormwater reported `inserted 0 / unchanged 12` and `inserted 0 / unchanged 19747`; rows `12/19747/5`; DB `string_agg(distinct data_class||':'||classification)` = `RODENT_REPORT:SIMULATED`; API `/api/v1/rodent-reports` → `available`, 5 features, attribution `RatSight synthetic rodent-report fixture` |
| V-SYNTHUI | browser with the synthetic rows loaded | Panel header `合成回報 / 鼠類回報 / SIMULATED · 模擬`, row `RODENT_REPORT · SIMULATED（模擬）`, `目前視窗與 Asia/Taipei 時間範圍（起迄皆含，請求以 UTC 邊界送出）內回傳 5 筆回報`, five timestamps listed; 18 `SIMULATED`/`合成` mentions on the page; 0 console errors |
| V-RECREATE | `down --purge` then default `up` | Rodent returned to 0 without any manual delete: `rodent_reports is empty: synthetic fixtures stay opt-in (pass --synthetic)` — the opt-in state is not sticky |

## Independent Municipal Analyst pass (V-MUNI)

`verification-municipal-analyst@rat-team` evaluated `http://127.0.0.1:3081` against the same
populated profile in a browser-only session (2026-10-23 08:31Z) and returned **PASS with limits**:

- Startup marked no real observations; pipeline loading state; `UNVERIFIED`/`SIMULATED` labels present.
- 12 districts visible; selected 松山區 showing `ADMINISTRATIVE_REFERENCE`/`UNVERIFIED`, dataset
  `121199` / resource `20220915`, official source URL, licence, and currentness.
- Pipeline view reported 5000 returned for the viewport with an explicit cap and no exact total,
  listed the first 100, and surfaced the 19,747-row quality warnings (missing pipe number 20,
  duplicate pipe numbers 310, missing start 992, missing end 991, missing notes 17950); selected
  `4752-p3-p4` with provenance, Z dropped, publisher-only connectivity warning,
  `INFRASTRUCTURE_REFERENCE`/`UNVERIFIED`.
- Zoom-in changed the visible list under the bounded cap.

This closes `tasks.md` task 11. The analyst left the runtime untouched; teardown is recorded below.
That pass is usability evidence on synthetic fixtures plus pinned reference layers. It is **not**
municipal acceptance, and it is not evidence of currentness, completeness, or connectivity.

## Suite and static checks (task 9)

| ID | Command | Exit | Result |
| --- | --- | --- | --- |
| V-PYTEST | `uv run pytest scripts/tests/test_data_bootstrap_script.py -q` | 0 | `6 passed in 1.89s` |
| V-BASHN | `bash -n scripts/data_bootstrap.sh` | 0 | no output |
| V-VITEST | `cd apps/web && corepack pnpm exec vitest run` | 0 | `Test Files 3 passed (3)`, `Tests 60 passed (60)` (57 before this change) |
| V-TYPE | `cd apps/web && corepack pnpm exec tsc --noEmit` | 0 | no diagnostics |
| V-LINT | `make lint` | 0 | `eslint .` + `uv run ruff check .` → `All checks passed!` |
| V-BUILD | `make build` | 0 | `next build` compiled, 3 static routes |
| V-OPEN | `corepack pnpm exec openspec validate bootstrap-full-local-data --strict` | 0 | `Change 'bootstrap-full-local-data' is valid` |

## Candidate assessment boundary (V-CANDIDATE)

- `services/api/src/ratsight_api/importers/` contains only `administrative_districts.py`,
  `rodent_reports.py`, `stormwater_pipelines.py` — no sewer, manhole, or trash-bin importer.
- Alembic versions end at `0006_rodent_reports_immutability.py`; no candidate-layer migration.
- `docs/infrastructure/full-local-data-bootstrap.md:123` "This profile ingests neither candidate
  and adds no importer for them."; `:131` "No additional candidate is approved for ingestion by
  this change."; `:133` public trash bins remain a conditional future candidate.
- `git status --porcelain` shows no path matching sewer/manhole/trash/污水/人孔.

## Findings

| ID | Severity | Status | Detail |
| --- | --- | --- | --- |
| QA-FLL-001 | MINOR | FIXED, re-verified | The spatial-context line rendered `無雨水下水道資料` when the viewport exceeded the 0.3° cap, although 19,747 rows were stored and the layer row correctly said `請放大`. Conflated "suppressed viewport" with "empty storage". Now `stormwaterContext` (`dashboard.tsx:224-232`) distinguishes 請放大載入 / 載入中 / 參考資料 / 尚未匯入 / 狀態未知. Verified in V-BROWSER2 |
| QA-FLL-002 | MINOR | CLOSED, probe limitation only | An earlier probe read the wrong DOM node and left the pipeline detail panel unasserted. Retried in V-BROWSER2; the panel renders all published attributes plus `資料類別`/`分類`. No product defect |

Independent Municipal Analyst browser pass completed on approved `http://127.0.0.1:3081` (API 8001, persistent DB 54330), browser-only and read-only. PASS: 12 districts, district provenance/source limitations, 5000-feature stormwater cap and no-total wording, 19,747-row quality warnings, pipeline selection/provenance, bounded zoom/pan behavior, and reference-only/UNVERIFIED limitations. No runtime mutation or source inspection.

## Limitations of this evidence

- Storage-empty, service-error, and unknown-state presentations were **not** exercised on this
  profile: all three layers were populated for the whole run. Their code paths exist
  (`尚未匯入邊界`, `尚未匯入雨水下水道`, `…狀態未知`) but no screenshot or assertion covers them here.
- One machine, one Docker engine, local filesystem. Cross-platform behaviour is unverified.
- Truncation was exercised at the 5000-feature cap; the exactly-5000 and 4999 boundaries were not.
- A Docker daemon restart or host reboot is documented as operator re-launch, not tested.
- The foreign process previously listening on `127.0.0.1:8000` (pid 16716, `uvicorn --reload`) was
  serving `/health` 200 at the start of this run and was **not** touched by any command here. At the
  end of the run `127.0.0.1:8000` answered `000` and no `uvicorn --reload` process remained; this run
  never signalled it, and the cause was not investigated. `127.0.0.1:3000` also answered `000` at the
  end. Recorded as an observation, not a verified cause.
- Counts 12 / 19,747 describe the pinned source records only. They are not evidence of
  currentness, completeness, connectivity, or traversability.

## Cleanup (V-TEARDOWN)

After the Municipal Analyst pass, QA owned the teardown of both app tiers — the QA processes and the
lead-launched PIDs recorded in `/tmp/ratsight-full-local-api.pid` and
`/tmp/ratsight-full-local-web.pid` — at `2026-10-23T08:33:49Z`:

- Listeners on 8001 and 3081: 0 (both ports free; `/tmp/qa-full-local/14-teardown.txt`).
- `ratsight-full-local-postgres-1` left running and populated at `12/19747/0` on 54330, per the
  lead's decision to keep the persistent profile rather than bring it down.
- Shared `infra-postgres-1` `Up 41 hours (healthy)`, shared volume `infra_ratsight-postgres-data`
  `CreatedAt 2026-10-15T16:34:38Z` unchanged.
- No `down --purge` was run on the profile after the analyst pass, so the reconstructible environment
  the lead owns is still there.
- `apps/web/tsconfig.json` was reverted after `next dev` appended the `.next-ratsight-full-local`
  type paths (`git diff --stat apps/web/tsconfig.json` empty).
