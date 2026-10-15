# Traceability Validation

`verification/gate.json` holds machine-checked traceability state. This
narrative summary is optional; the quality gate does not parse it.

Engineering requirement identifiers must exactly match OpenSpec output:
`<spec-name>#<requirement-name>`. Map each changed requirement to implementation
files, test files, verification-run IDs, and a status. Do not invent a
requirement to fill a gap.

When science applies, record exact evidence IDs and source files, assumptions,
parameters, models, data classifications, validation-run IDs, and limitations.
Otherwise set `science.applicable` to `false` with a reason. Keep `OBSERVED`,
`INFERRED`, `SIMULATED`, and `UNVERIFIED` distinct; unknown values stay
unknown. A recorded trace is not proof of scientific validity.
