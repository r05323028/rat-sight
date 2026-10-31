# Traceability Validation

`verification/gate.json` holds machine-checked traceability state. This narrative summary is
optional; the quality gate does not parse it. Write it when a reviewer needs to judge the mapping.

Engineering requirement identifiers must exactly match OpenSpec output:
`<spec-name>#<requirement-name>`. Map each changed requirement to implementation files, test files,
verification-run IDs, and a status. Do not invent a requirement to fill a gap.

## Behavioral mapping

For each applicable requirement, record:

- **Expected observable behavior** — what a caller or user can observe if the requirement holds.
- **Implementation** — the file and symbol that produces it, not just the file.
- **Test and how it exercises the behavior** — the test name, the input it drives, and the assertion
  that would fail if the behavior regressed.
- **Missing negative and boundary scenarios** — what is not exercised: invalid input, empty sets,
  authorization failure, timeouts, concurrency, CRS/unit edges.
- **Verified or inferred** — say which. "The test file exists" and "the scenario comment names this
  requirement" are not verification. Inferred coverage belongs in `gap`.
- **Unsupported claims** — completion, accuracy, or performance statements that no check supports.

A test name, scenario comment, or file path is a pointer, not proof. If you did not run or read the
assertion, record the requirement as `PARTIALLY_VERIFIED` with the gap.

## Status rules

- `VERIFIED` — implementation and test files exist, every cited verification ID exists, and the
  behavioral mapping above explains how the test exercises the requirement.
- `PARTIALLY_VERIFIED` — write the remaining `gap`. Under `schema_version: 3` this blocks readiness;
  incomplete verification is not success.
- `NOT_APPLICABLE` — only for requirements the change removes, with the reason in `gap`. A changed or
  added requirement cannot be declared inapplicable.
- `UNVERIFIED` — always blocks.

Every verification `reference` must resolve to a file in this repository (relative to the repository
root or the change directory) or be an explicit `ci:` or `https:` reference. Resolution proves the
artifact exists, not that the command ran.

Prefer captured test output, a CI run, or an artifact the recorded command produced. An
agent-authored report can carry a claim that has no machine artifact, but say so in the entry: a file
that only restates the claim is a pointer, not evidence that the behavior holds.

When science applies, record exact evidence IDs and source files, assumptions, parameters, models,
data classifications, validation-run IDs, and limitations. Otherwise set `science.applicable` to
`false` with a reason. Keep `OBSERVED`, `INFERRED`, `SIMULATED`, and `UNVERIFIED` distinct;
unknown values stay unknown. A recorded trace is not proof of scientific validity.
