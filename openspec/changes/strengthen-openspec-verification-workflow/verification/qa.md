# Quality assurance — strengthen-openspec-verification-workflow

> **Retrospective record.** The change was implemented before this record existed. The commands
> below were run on 2026-10-30 from `/Users/seanchang/rat-sight` against the working tree that
> contains this change. No CI run has happened for this change set, so every line is local
> execution evidence, not a CI artifact. The reviewer is the implementing agent.

## Scope

Covers the evidence-driven OpenSpec hardening: frozen `schema_version` rule, changed-only CI
validation and its base resolution, shared task-marker counting, gate/acceptance agreement,
evidence-reference resolution and templates, the `--skip-openspec` policy, upstream instruction
preservation, and the benchmark labels. It does not touch the web app, the API, PostGIS, the geo
or simulation packages, movement data, or any scientific claim.

## Automated checks

| Check | Command | Result |
| --- | --- | --- |
| Full scripts suite | `uv run -- python -m pytest scripts/tests -q` | 101 passed in 636.31 s |
| Benchmark label tests | `uv run pytest scripts/tests/test_openspec_benchmark_labels.py -q` | 3 passed |
| Lint | `uv run ruff check .` | All checks passed |
| Types | `uv run basedpyright` | 0 errors, 0 warnings, 0 notes |
| Schema | `openspec schema validate evidence-driven` | valid |
| Change structure | `openspec validate strengthen-openspec-verification-workflow --strict` | valid |
| This change's gate | `uv run python scripts/openspec_quality_gate.py strengthen-openspec-verification-workflow --json` | PASS (readiness), 12/12 tasks, 6 verification runs, 7 mapped requirements |
| Legacy compatibility | gate over the 16 frozen records | decisions unchanged: the same 7 pass, the same 9 remain blocked for pre-existing reasons; each now also warns `GATE-RECORD-LEGACY` |

The suite covers the bypass regressions directly: version freeze, PR/push/shallow/missing-base
resolution, the [ ], [x], [X], [~], [-], [] marker matrix, and the readiness skip policy.

## Not run

- GitHub Actions itself: the event paths are simulated in disposable repositories (AR-10).
- `services/api`, `packages/geo`, `packages/simulation`, web tests, browser smoke: this change
  touches review tooling only, so those suites were not exercised.
- Owner acceptance: `review/status` shows `owner_acceptance_pending: true`; no decision exists.

## Limitations

- `verification/gate.json` records references and exit codes; the gate cannot authenticate that
  these commands ran as written. This file and the review reports are the claim; the test files
  are the checkable part.
- A legacy record can still be edited under `schema_version: 2`; the gate warns
  `GATE-RECORD-LEGACY` but does not force migration (AR-8).
- The evidence above was produced locally, not in CI.
