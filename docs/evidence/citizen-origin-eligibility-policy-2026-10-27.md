# Citizen-report origin eligibility policy (engineering baseline)

- Evidence ID: EVID-CITIZEN-ORIGIN-ELIGIBILITY-2026-10-27
- Date: 2026-10-27
- Data class: UNVERIFIED (citizen-report aggregate input) / SIMULATED (movement output)
- Status: PARTIALLY_VERIFIED — enforcement is implemented and tested; the policy itself is not scientifically approved.

## Policy

`sighting` reports are the only eligible candidate-origin category (`origin-report-category-v1`). `bait_station` and `other` (and any unrecognized type) remain displayable context-only reports with a disabled simulation action. The rule exists once, in `origin_eligibility()`.

## Rationale, stated as assumptions rather than facts

- **Sighting eligibility:** a report typed as a sighting is the closest available coarse signal that a rodent was reported nearby. It is still an unverified public report, not an observation, and a 250 m cell never identifies an actual animal location.
- **Bait-station exclusion:** a poison-bait report records intervention hardware or activity, not an animal. Treating it as an origin would confuse control effort with rodent presence.
- **Other exclusion:** the residual category has no defined semantics, so it cannot be assumed to indicate rodent activity.
- **Counts are not animals:** report counts mix reporting propensity, platform use, and population; they are never simulation weights or abundance estimates.
- **Uniform graph-node seeding is an engineering baseline:** every strictly in-cell node is an equally plausible street location for a synthetic walker because no sub-cell location evidence exists. It is not rodent ecology.
- **Road geometry is not movement ecology:** the OSM surface network constrains where synthetic walkers may go; it does not establish that real rodents follow those edges.
- **Remaining hypothetical assumptions:** reporting bias, the 250 m cell as a meaningful origin unit, uniform node seeding, and the weighted random-walk transition model are all unvalidated for Taipei.

## Approval state

Public-health and mathematical-modeler review of this policy is pending. No approval is claimed here, and engineering tests prove enforcement only.
