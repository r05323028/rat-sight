# Full local data bootstrap

Persistent, pinned reference data for local dashboard work. Design and gates live in
`openspec/changes/bootstrap-full-local-data/`; this page is the operator contract.

## What it does

`make data-bootstrap` starts a PostGIS instance in its **own Compose project**
(`ratsight-full-local`) with its **own named volume**
(`ratsight-full-local-postgres-data`), applies migrations, and runs the two verified
official importers:

| Layer | Source identity | Pinned records | Classification |
|---|---|---|---|
| `administrative_districts` | dataset `121199`, version `20220915`, SHA-256 `77bcc347b503b8ff8a43f7e1afaaedb18877a6222282587b145adaba69afd2d9` | 12 | `ADMINISTRATIVE_REFERENCE` / `UNVERIFIED` |
| `stormwater_pipelines` | dataset `97b82d58-faba-4ee4-9488-dd5d04a79efd`, resource `5240223d-5187-454e-b323-63443a195639`, version `2026-02-23T17:10:41Z`, SHA-256 `5d2ea04f7d032d21b07066310e80eb64a34ce8916b4a0c786b10948aeb4e10e4` | 19,747 | `INFRASTRUCTURE_REFERENCE` / `UNVERIFIED` |
| `citizen_report_cells` (opt-in) | no pinned export; the content hash is recorded per import (observed: `eae7182b7f1cb57a73c1c074e732a8d5780da0cbdc7c481c3972ec7f3c23c24b`) | 91 suppressed cells / 319 reports | `CITIZEN_REPORT_AGGREGATE` / `UNVERIFIED` |

Evidence: `docs/evidence/taipei-district-boundaries-2026-10-15.md`,
`docs/evidence/taipei-stormwater-network-2026-10-16.md`,
`docs/evidence/taipei-stormwater-acceptance-2026-10-16.md`,
`docs/evidence/ratdar-reuse-claim-2026-10-26.md`.

The shared development database (`infra` project, port 54329, volume
`infra_ratsight-postgres-data`) is never started, migrated, written, or deleted by this
command. That is why the profile uses port 54330 and its own volume.

## Commands

```sh
make data-bootstrap                      # up: verify sources, migrate, import, inventory
make data-bootstrap ARGS=--inspect-only  # verify sources only: no DB writes, no downloads
make data-bootstrap ARGS=status          # container state, counts, provenance, local sources
make data-bootstrap ARGS=down            # stop containers, keep data
make data-bootstrap ARGS="down --purge"  # explicitly recreate from empty (destructive)
make data-bootstrap ARGS=--synthetic     # additionally load the SYNTHETIC rodent fixture
make data-bootstrap ARGS="up --citizen-reports"  # suppressed 250 m citizen counts (never downloads)
```

`PROFILE=full-local` is the only supported profile; anything else exits `2`.

Exit codes: `0` ok, `1` fail-closed integrity problem (hash/count) with data unchanged,
`2` unusable input (bad profile/argument, missing source), `3` environment unavailable
(no Docker, port busy) or importer conflict, `4` importer storage error.

## Sources

Raw licensed archives stay **outside Git** and are never committed. Default location:

```
${XDG_DATA_HOME:-$HOME/.local/share}/ratsight/full-local/
  districts-121199-20220915.zip
  stormwater-5240223d-2026-02-23.xml
```

The default simulation study area also needs the pinned OSM surface extract at
`${XDG_DATA_HOME:-$HOME/.local/share}/ratsight/network/taipei-songshan-20261023.osm`
(SHA-256 `faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e`). This profile
does not download it: provision it with `scripts/fetch_taipei_osm_source.sh` (see
`docs/infrastructure/taipei-osm-network-source.md`). Without it the default preview returns
`503 SOURCE_NETWORK_UNAVAILABLE` instead of falling back to the schematic graph.

Overrides: `RATSIGHT_FULL_LOCAL_DATA_DIR`, `RATSIGHT_DISTRICTS_ARCHIVE`,
`RATSIGHT_STORMWATER_SOURCE`, `RATSIGHT_CITIZEN_REPORT_SOURCE`. The base data directory is
also honoured by `data/raw/README.md`.

If a file is missing, `up` downloads only the two documented verified URLs, verifies the
exact pinned SHA-256, and aborts before any import on mismatch (`*.part` is removed). It
never substitutes a different source. `--inspect-only` never downloads.

Before any write, both sources are validated by the importers' own inspect-only mode:
archive/file hash, required shapefile components, CRS transformation (`EPSG:3826` →
`EPSG:4326`), geometry types, zone-3D handling for stormwater, source identity, and the
pinned record counts.

## Idempotency

Rerunning the same command with unchanged sources is a no-op by design:

- administrative boundaries: identical content hash → `unchanged`, no duplicate rows;
  a different archive hash for an existing version is a conflict (exit `3`), and
  deletions are never implicit;
- stormwater: same identity set and content → `unchanged`; any changed record or
  identity set for an existing version is a conflict (exit `3`), never an overwrite;
- citizen aggregates: an identical content hash reuses the stored version, so re-running on
  the same export inserts `0` rows and adds no new version.

The bootstrap never truncates, resets, or replaces data. To start over, recreate the
volume explicitly with `ARGS="down --purge"`, then `make data-bootstrap`.

### Not atomic across layers

Each importer commits in its own transaction, so the profile is **not** atomic across the
two layers. If stormwater fails after administrative boundaries committed, exit `3`/`4`
is returned, the boundary rows stay imported, and the script says so instead of claiming a
clean rollback. Rerunning completes the remaining layer; `ARGS=status` shows what is
present. Nothing is ever replaced to "repair" a partial run.

## Runtime tier

Nothing supervises the API/Web tier. After a Docker daemon restart or reboot the database
comes back on its own; re-run the app tier:

```sh
export DATABASE_URL="postgresql+psycopg://ratsight:ratsight_dev_only@127.0.0.1:54330/ratsight"
uv run --package ratsight-api uvicorn ratsight_api.main:app --host 127.0.0.1 --port 8000
NEXT_PUBLIC_API_URL="http://127.0.0.1:8000" corepack pnpm --filter @ratsight/web dev \
  --hostname 127.0.0.1 --port 3080
```

Port 3080 avoids the listeners (for example a proxy on 3000) that commonly occupy the
default Web port; the bootstrap never inspects or stops processes it did not start.

The repository `.env` ships `DATABASE_URL` on port 54330 (this profile) so `make api` and
`uvicorn --reload` reach the populated database without an extra export; the shared `infra`
profile on 54329 starts empty and lacks the citizen-aggregate table until migrated.

## Optional synthetic layer

`--synthetic` imports the immutable committed rodent-report fixture. It stays
`RODENT_REPORT` / `SIMULATED`, and the default profile leaves `rodent_reports` empty so
simulated rodent movement is never mistaken for observation. See
`docs/infrastructure/rodent-reports-import.md`.

## Optional citizen-report aggregate layer

`--citizen-reports` imports a public citizen-report export into **suppressed 250 m cell
counts only**: no coordinates finer than the cell, no free text, no photo links, no
per-report rows. Optional fields present in the export (地點, 說明, 照片網址) are dropped by
the importer and never reach the database. Cells with fewer than 3 reports are excluded
entirely, so absence means "suppressed or unreported", not zero.

The layer stays `CITIZEN_REPORT_AGGREGATE` / `UNVERIFIED` and is never a simulation input.
Reuse terms for the export are **unverified** (owner assertion recorded in
`docs/evidence/ratdar-reuse-claim-2026-10-26.md`), which is why the import is opt-in and the
source file stays outside Git (`data/raw/*` is ignored).

## Reading the inventory

The inventory prints row counts plus `dataset_id@resource_version` per table. Those counts
describe **the pinned source records only**. They do not establish currentness,
completeness, connectivity, traversability, rodent movement, prevalence, risk, or
intervention effect. The stormwater publisher states the network map is reference only.

The API keeps its existing bounded behaviour: `BBOX_MAX_SPAN` 0.30°, `FEATURE_CAP` 5000.
With 19,747 stormwater records, an unfiltered request returns `truncated: true` with 5000
features and `feature_count` describing the returned count, never a total — the dashboard
must stay viewport-bounded instead of claiming a full-city count.

## Candidate layers: assessment only

This profile ingests neither candidate and adds no importer for them.

| Candidate | Status | Reason |
|---|---|---|
| Public trash bins | CONDITIONAL NO-GO | Publisher CRS/axis order unresolved; catalog currentness ends 2018-01-10 (`docs/evidence/public-trash-bin-feasibility-2026-10-18.md`) |
| Sanitary sewer pipelines | NOT IDENTIFIED | No verified source identity, license, or CRS; no bulk fetch is authorized |
| Sewer manholes | NOT IDENTIFIED | Same; surface geometry would not establish sewer connectivity |

No additional candidate is approved for ingestion by this change. Stormwater Candidate B is
already the recommended supported reference layer because its CRS, stable identifiers, and
hash are verified. Public trash bins remain a conditional future candidate only after the
publisher confirms CRS/axis order, identity, and currentness.

## Related

- `openspec/changes/bootstrap-full-local-data/` — proposal, design, spec, tasks, adversarial review
- `docs/infrastructure/administrative-boundaries-import.md`
- `docs/infrastructure/stormwater-pipelines-import.md`
- `scripts/verify_official_districts.sh` — one-time disposable official-source verification
