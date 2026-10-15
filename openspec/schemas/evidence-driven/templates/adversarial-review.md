# Adversarial Review

Complete before `tasks.md`.

Challenge assumptions, requirements, design, evidence, scientific validity,
and failure cases. Record findings, rationale, and resolutions in prose; no
prescribed headings or table format.

Record the decision and finding IDs, severity, and status in
`verification/gate.json`. The gate requires this report and validates recorded
review state, but does not inspect report contents.

Resolve every `BLOCKING` finding before tasks. Blocking findings cannot be
waived. Non-blocking `ACCEPTED_RISK` needs human approval tied to the exact
finding ID in `gate.json`.
