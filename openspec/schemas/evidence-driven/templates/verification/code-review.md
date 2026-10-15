# Independent Code Review

After implementation, inspect the actual diff and relevant surrounding code
from a reviewer context separate from the implementer.

Record findings, evidence, corrections, rechecks, and residual risks in clear
prose. Put decision state and finding IDs, severity, and status in
`verification/gate.json`.

The quality gate requires this report and checks recorded state; it does not
parse the report or prove that a separate context was used. Record available
context evidence and any limits honestly. Self-review cannot satisfy this
mandatory review.
