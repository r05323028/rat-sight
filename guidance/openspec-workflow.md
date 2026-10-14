# OpenSpec workflow checkpoints

OpenSpec's local schema is the installed `spec-driven` workflow fork. Its structural artifacts are proposal, specs, design, and tasks; it does not encode every RatSight lifecycle stage. Lead owns coordination and must not report unsupported stages as CLI-enforced.

For each change:

1. **Research and evidence:** Researcher records verifiable sources in `docs/evidence/`; use evidence IDs and note location, species, method, applicability, limitations, and confidence. Unknowns remain unknown.
2. **Proposal and specifications:** Create a change using `openspec new change <name>`. State motivation, boundaries, data classes, assumptions, and evidence links. Requirements define observable behavior, not scientific conclusions.
3. **Design:** Separate observed, inferred, simulated, and unverified data paths. Model changes state parameters, units, provenance, assumptions, reproducibility, uncertainty, and validation plan.
4. **Adversarial review:** Before implementation, reviewer challenges evidence fit, assumptions, safety, alternatives, and falsifiability. Resolve blockers in proposal/spec/design.
5. **Implementation:** Only after review, execute tasks. Engineering work follows Spec → Implementation → Tests → Review. Preserve independent package boundaries and deterministic seeds.
6. **Independent code review:** Reviewer examines diff and connected code, not author summary alone; record evidence-backed findings.
7. **QA and scientific validation:** QA runs tests, API/UI behavior, reproducibility and regression checks. Modeler/researcher document validation limits; no fabricated accuracy metrics.
8. **Traceability and acceptance:** Map claims/parameters to evidence and tests; verify no simulated path is presented as observation. Lead accepts only with verification evidence. Significant architecture or scientific-assumption changes require human approval.
9. **Archive:** Validate with `openspec validate <name>` and `openspec schema validate evidence-driven`; archive only after all project checkpoints pass.

Use the CLI's supported artifacts and template fields only. Keep additional review records in repository docs or change artifacts; do not add unsupported schema keys.
