# RatSight — First Black-box Usability Review

> Research and usability assessment. This is not an official Taipei City Government evaluation; the municipal analyst is a simulated persona.

## A. Evaluation environment

- **URL:** `http://localhost:3000`
- **Browser capability:** `ego-browser`
- **Data state:** Built-in synthetic fixture available; fresh install, real data, and populated official-dataset scenarios were not run.
- **Initial-pass limits:** No source code, API, tests, technical documentation, or hidden state were inspected. No code, database, or shared state was modified.
- **Follow-up review:** QA independently reproduced UX-001 through UI-only, read-only interaction. Public-health reviewed scientific interpretation.
- **Evidence:** `/tmp/ratsight-top2.png`, `/tmp/ratsight-simulation-map.png`, `/tmp/qa-ux1-20261018/ux1-after-run-full.png`, `/tmp/qa-ux1-20261018/ux1-results-viewport.png`, `/tmp/qa-ux1-20261018/ux1-map-paths-on.png`

## B. First impression

Purpose is broadly understandable: a workspace for urban movement analysis and decision support. The interface clearly shows `No real observation data loaded`, `SIMULATED`, and `No ... imported/loaded`, allowing a careful user to recognize the data boundary.

However, the map and simulation controls may still lead users to expect real administrative analysis. The `Analysis` panel presents values with a visual treatment similar to real metrics.

## C. User journey

| Task | Status | Main observation |
|---|---|---|
| Understand the product | COMPLETED | Understandable as a data and simulation demonstration workspace |
| Discover datasets | COMPLETED | Five synthetic rodent reports were discoverable |
| Explore geographic context | PARTIALLY COMPLETED | Basemap and coordinates available; districts, pipelines, and other layers not loaded |
| Investigate rodent information | COMPLETED | Data explicitly identified as synthetic and not verified observations |
| Interpret results | PARTIALLY COMPLETED | Simulation can run, but real risk or hotspot conclusions cannot be drawn |
| Support administrative decisions | NOT AVAILABLE | Insufficient basis for inspection prioritization or resource allocation |

The default synthetic preview produced reproducible results: seed 42, 312 node visits, and 16 synthetic edges. The interface also showed `Not estimated`, `Not quantified`, and stated that simulated paths are not observed animal migration routes.

## D. UX findings

### UX-001: Simulation output can be mistaken for administrative analysis

- **User goal:** Determine whether RatSight can support investigation and decisions about rodent-related issues in Taipei.
- **OBSERVED:** A synthetic preview can be run, showing 312 node visits and 16 synthetic edges; QA reproduced the same values on a second seed-42 run.
- **OBSERVED:** The interface shows `SIMULATED`, `Not estimated`, `Not quantified`, and `No real observation data loaded` warnings.
- **OBSERVED:** Before execution, there is not a sufficiently prominent statement that hotspot, risk, or movement inferences must not be made; results appear in a panel titled `Analysis`.
- **EXPECTED:** Before execution and beside results, clearly state that the data and output are synthetic fixtures and cannot support real administrative decisions.
- **IMPACT:** Careful users are unlikely to overclaim, but ordinary users may read 312/16 as analytical results.
- **Classification:** Scientific interpretation concern
- **Severity:** MAJOR
- **Evidence:** Screenshot paths above; independent QA UI-only reproduction.
- **Recommendation:** Use `Synthetic preview — simulated fixture only; no real observations` and place this next to `Uncertainty not estimated; do not infer prevalence, movement, risk, hotspots, completeness, or intervention effect`.

### UX-002: Unloaded layers provide no next-step guidance

- **OBSERVED:** Administrative districts, stormwater pipelines, sewer networks, and other layers are visible but show `No ... imported/loaded`.
- **EXPECTED:** Users should know whether data is absent, how it could be obtained, and what they can do next.
- **Classification:** Missing capability / environment-setup issue
- **Severity:** MINOR
- **Recommendation:** Show data status, source/licensing requirements, and next-step guidance instead of presenting missing data as a simple disabled checkbox.

### UX-003: Date filtering is unintuitive

- **OBSERVED:** UTC is used; year, month, day, AM/PM, and time are split across multiple controls. Correct filter application was not verified.
- **EXPECTED:** Municipal analysts should have an understandable date range control and clear timezone guidance.
- **Classification:** Usability defect
- **Severity:** MINOR
- **Recommendation:** Provide a clear date range, timezone explanation, and filtered-record count.

## E. Capability gaps

The interface currently lacks:

- Real or verified rodent observations
- Administrative district, stormwater/sewer, environmental, and human-activity data
- Statistical summaries, risk estimates, and quantified model uncertainty
- Evidence sufficient to prioritize real Taipei inspections

Fixture content is `SIMULATED`, not `OBSERVED`. It must not support claims about prevalence, incidence, infestation, population, movement/migration, disease risk, hotspots, completeness, or intervention effect. `Uncertainty` is `NOT ESTIMATED/UNVERIFIED`; it is not zero and does not imply confidence.

## F. Top three improvements

1. On the first screen, clearly separate “can do: dataset catalog and demonstration” from “cannot do: real hotspots, risk, or route inference.”
2. Give unloaded layers explicit data status and user next steps.
3. Use an understandable date range, explain the timezone, and show the filtered record count.

## G. Recommendation

The smallest coherent next OpenSpec change is to improve data-status messaging and synthetic-simulation interpretation messaging; address UX-001 first, then improve layer next steps and date-filter comprehension.

**Out of scope:** Real-data import, a new risk model, administrative prioritization, report export, and mobile/accessibility improvements.

RatSight is currently suitable as a provenance-aware synthetic demo, not as a real rodent-control decision tool. Real-data work should first provide source, licensing, CRS, temporal coverage, and uncertainty information, followed by another workflow evaluation.

## H. Untested items and limitations

- Fresh install
- Populated official dataset
- Real data
- Data-import workflow
- Individual district/pipeline feature inspection
- Date-filter correctness
- Comparison of multiple simulation parameters/interventions
- Download/report export
- Mobile/accessibility
- Effect of seed on path geometry

This report describes a simulated-persona black-box observation and does not represent validation by a government employee or Taipei City Government. No OpenSpec change or gate artifact was created, and no application or shared data was modified.
