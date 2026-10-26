# Code review

Decision: PASS for scoped frontend implementation.

## Findings

- CR-001 (MAJOR): synthetic output could read as analysis — RESOLVED by orientation panel, pre/post simulation warnings, `SIMULATED` labels, and mode-specific result copy.
- CR-002 (MAJOR): unavailable data could read as zero — RESOLVED by explicit unavailable/loading/empty guidance and source-import link.
- CR-003 (MAJOR): technical controls dominated first-run flow — RESOLVED by sensible defaults, advanced disclosure, date presets, and collapsed provenance.
- CR-004 (MAJOR): aggregate and trajectory modes could be conflated — RESOLVED by mode-specific summaries, trajectory IDs/edge counts, and automatic path-layer visibility.
- CR-005 (MINOR): high-risk metadata was hidden — RESOLVED by provenance disclosure listing returned fields and `未提供` for absent fields.
- CR-006 (MINOR): reduced-motion camera animation and small layer targets — RESOLVED by zero-duration `fitBounds` under reduced motion and 24×24 layer checkboxes; QA recheck confirmed all five layer controls meet target.
- CR-007 (MAJOR): trajectory clicks could miss the visible 3px stroke — RESOLVED with a transparent 16px hit layer sharing trajectory geometry; coordinate-click browser regression passes.

No API or backend change required. Existing network-aligned movement behavior remains outside this frontend redesign diff and must retain its separate source/hash review.
