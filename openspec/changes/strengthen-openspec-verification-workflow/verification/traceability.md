# Traceability — strengthen-openspec-verification-workflow

Review records: `adversarial-review.md` (post-implementation) and `verification/code-review.md`.
References are pointers; they resolve to files or `ci:` identifiers, and the gate cannot prove
that a command ran or that a recorded judgment is right.

| Requirement | Implementation | Tests | Verification |
|---|---|---|---|
| `openspec-verification-workflow#Frozen legacy record version` | `scripts/openspec_quality_gate.py` | `scripts/tests/test_openspec_quality_gate.py` | V1 |
| `openspec-verification-workflow#Non-vacuous changed-only CI validation` | `scripts/openspec_validate_changed.py`, `.github/workflows/ci.yml` | `scripts/tests/test_openspec_validate_changed.py` | V1 |
| `openspec-verification-workflow#Consistent task marker counting` | `scripts/openspec_tasks.py`, `scripts/openspec_quality_gate.py`, `scripts/change_acceptance.py` | `scripts/tests/test_openspec_tasks.py`, `scripts/tests/test_openspec_quality_gate.py` | V1 |
| `openspec-verification-workflow#Evidence references are pointers` | `scripts/openspec_quality_gate.py`, `guidance/openspec-workflow.md`, `openspec/schemas/evidence-driven/templates/verification/gate.json` | `scripts/tests/test_openspec_quality_gate.py` | V1 |
| `openspec-verification-workflow#Skip-openSpec is planning-only` | `scripts/openspec_quality_gate.py`, `Makefile` | `scripts/tests/test_openspec_quality_gate.py` | V1 |
| `openspec-verification-workflow#Upstream schema instructions are preserved` | `openspec/schemas/evidence-driven/schema.yaml` | `scripts/tests/test_openspec_schema.py` | V2 |
| `openspec-verification-workflow#Illustrative benchmark labelling` | `docs/benchmarks/openspec-review-workflow.json` | `scripts/tests/test_openspec_benchmark_labels.py` | V3 |

Verification ids are declared in `verification/gate.json`. Compatibility evidence: the 16 frozen
records keep their decisions (V4); the retrospective record itself is the only active change that
gains errors from this work.
