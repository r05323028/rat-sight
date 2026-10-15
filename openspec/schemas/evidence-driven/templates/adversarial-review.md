# Adversarial Review

Complete before `tasks.md`, from a reviewer context separate from the
proposal, specifications, and design author.

Write a readable challenge of assumptions, requirements, design, evidence,
scientific validity, and failure cases. Record findings, rationale, and
resolutions in prose; no prescribed headings or table format.

Record decision state and finding IDs, severity, and status in
`verification/gate.json`. The gate checks that this report exists, not its
contents. It cannot prove that a review happened or authenticate independence.
Identity and context references are provenance, not proof. State limitations
when independence evidence is unavailable; self-review does not satisfy the
mandatory independent-review requirement.

Resolve every `BLOCKING` finding before tasks. Blocking findings cannot be
waived. Non-blocking `ACCEPTED_RISK` needs human approval tied to the exact
finding ID in `gate.json`.
