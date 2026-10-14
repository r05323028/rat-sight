# Mathematical modeling roadmap

Initialization implements only a synthetic, seeded weighted random walk to prove package/API/UI contracts. It is not an ecological population model, calibrated movement model, or municipal risk estimate.

Future sequence:
1. Specify species, spatial layers, units, temporal resolution and intended decisions with domain experts.
2. Review evidence for movement constraints and interaction with sewer/stormwater/surface layers; document all transfers and unknown parameters.
3. Define multilayer graph semantics, time-varying edge costs, behavior constraints and intervention counterfactuals before implementation.
4. Establish deterministic transition and Monte Carlo interfaces, seed capture, provenance and uncertainty outputs.
5. Design calibration only where representative observations exist; separate calibration and predictive validation datasets in time/space.
6. Run sensitivity/uncertainty and adversarial model review; report limits and observation bias.
7. Validate municipal use with independent data and stakeholders before decision support. No performance claims without held-out evidence.

Required chain: Evidence → Assumptions → Model → Validation. Never treat simulated trajectories as observed routes.
