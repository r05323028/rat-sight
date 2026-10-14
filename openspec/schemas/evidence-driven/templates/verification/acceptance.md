# Human Acceptance

<!-- Human acceptance is a human-controlled decision, never an agent's. Fields
     below are read by python3 scripts/openspec_quality_gate.py <change>. The
     gate fails on a missing approval when acceptance is required, on a
     placeholder approver or reference, and on agent consensus recorded as an
     approval. Do not write this file's approval fields until a human decision
     actually exists.

     Runtime note: the reference is an opaque pointer chosen by whoever recorded
     the decision. No specific approval transport, tool, or orchestration
     framework is required. -->

## Acceptance Record

- Change: <change-name>
- Human Acceptance Required: YES | NO
- Required per: NONE | ARCHITECTURE_CHANGE | NEW_SCIENTIFIC_ASSUMPTION | UNKNOWN_PARAMETER_DEFAULT | SENSITIVE_DATA_POLICY | ACCEPTANCE_EXCEPTION
- Non-applicability reason (required when Human Acceptance Required is NO and Required per is NONE):
- Approver (human identity and role):
- Approval reference (path to a decision record, an external decision id in any
  '<scheme>:<id>' form, or a recorded exchange the approver can point to):
- Approved at (UTC):
- Scope of approval:
- Decision: APPROVED | REJECTED | PENDING
- Agent consensus used as approval: NO
