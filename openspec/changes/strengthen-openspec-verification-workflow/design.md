# Design — retrospective workflow hardening

> **Retrospective record.** Predictions were not captured before implementation, so this document
> records the design that was implemented and the acceptance review that judged it, not a plan that
> existed beforehand.

## Context

The workflow consists of a schema (`openspec/schemas/evidence-driven/schema.yaml`), a quality gate,
an owner-acceptance CLI, a changed-only CI validator, and guidance documents. The gate and the
acceptance CLI already shared task counting badly, and the CI validator inferred its own diff base.

## Decisions

- **Freeze, do not migrate, version 2.** The sixteen existing records keep version 2. Their names
  are the allowlist; a record's identity is its change directory, so a renamed or new change cannot
  inherit the exemption. A legacy change that is materially edited can declare version 3 to get
  strict checks. Version 2 on any other change is an error and is still evaluated as v3, so the
  downgrade never removes checks. Rejected alternative: rewriting sixteen historical records, which
  would have fabricated review evidence they never had.
- **Make the base explicit and its absence fatal.** Push events use `GITHUB_EVENT_BEFORE`, pull
  requests use `origin/$GITHUB_BASE_REF`, and anything else falls back to `origin/main` then
  `main`. A base equal to HEAD is the shallow-checkout signature and fails with an actionable
  message. A diff that fails is an error. Only a resolved range with no OpenSpec paths is a
  zero-change success, and the payload distinguishes it with `evaluated: 0` and a note.
- **One parser for task markers.** `scripts/openspec_tasks.py` accepts bracketed markers of up to
  three characters that consist of marker characters, so `- [API] x` stays prose. Only `x`/`X`
  is complete; other non-empty markers count as unfinished and are reported. Excluded sections still
  reject unchecked boxes.
- **Evidence references stay pointers.** The template now asks for a CI run or artifact reference.
  Resolution to a repository file is necessary but not sufficient; the guidance says so explicitly,
  and an agent's own report is only acceptable when the entry names it.
- **Skip is a planning tool.** `--skip-openspec` keeps the CI-independent planning path and turns
  into an error at readiness, so a final acceptance cannot silently omit requirement coverage.
- **Upstream text is additive.** The apply instruction is the upstream line plus a project
  paragraph; the earlier replacement is reverted.

## Predicted behavior and impact

Not recorded ahead of implementation. Observed behaviour after the fact is captured by the
regression tests: a new change declaring version 2 is blocked, a shallow checkout exits 2, and
`[~]`/`[-]` items are counted and warned about. Behaviour outside those tests was not measured.

## Risks accepted

- An intentional task deletion is still undetectable; the workflow compares counts, not baselines.
- A vacuous test still counts as verification; the gate checks that evidence exists, not that it is
  meaningful.
- The legacy allowlist is a static list; adding a change that legitimately needs version 2 requires
  editing the file and is itself visible in review.
