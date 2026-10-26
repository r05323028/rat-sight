# Design

## Direction

Keep “Signed Inspection Sheet” visual language. Change structure, not brand: map stays focal; rail becomes task-oriented progressive disclosure.

## Information architecture

1. Orientation: purpose, evidence status, currently answerable/not answerable.
2. Map context: geographic reference, selected feature summary, layer controls.
3. Synthetic demonstration: primary `開始模擬` action; sensible defaults; advanced settings disclosure.
4. Records: synthetic report-shaped fixture inspection and date presets.
5. Provenance: collapsed technical details adjacent to outputs.

## Interaction rules

- Show synthetic/non-inference warning before and after simulation.
- Keep report and simulation surfaces separate; co-location never implies validation.
- Keep unavailable states actionable and distinguish unavailable from zero.
- Preserve loading, empty, filtered-empty, viewport-suppressed, service-error, and available states.
- Keep report layer off by default; user explicitly enables it.
- Use Asia/Taipei date labels; conversion to UTC remains implementation detail.

## Scope

Frontend-only unless existing API contract lacks a required state. No new dependencies or state framework. Preserve map query bounds, provenance, classifications, and unrelated worktree changes.
