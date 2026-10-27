# Human escalation

This file is the OpenRig-specific route for the runtime-independent escalation
requirement in `guidance/openspec-workflow.md`. Other runtimes use their own
human-approval channel; the workflow only requires that the decision be recorded.

Lead requests human judgment for material architecture changes, new scientific assumptions, unknown parameter defaults, sensitive-data policy, or accepted-risk exceptions. Present the decision, alternatives, evidence/assumptions, impact, and reversible path; pause affected work until answer. Do not use agent consensus as human approval. This policy approval is distinct from final project-owner acceptance: after verification, the owner uses the local `make change-review` / `make change-accept` CLI, not an agent gateway.

OpenRig's supported route is its human gateway plus durable queue, not an invented Pi dialog API. Register/configure the human only through `rig gateway human` commands; external connector credentials stay in external secret references. Create a durable decision item, park it on the configured human-seat session using `rig queue block` with summary, evidence reference, continuation, and wake, then resolve with `rig queue resolve --decision`. See `.openrig/README.md` and installed `rig queue ... --help` for exact session and required flags. If no human gateway/connector is configured, escalate through the project owner's existing manual OpenRig queue/terminal workflow; do not claim an interactive request was sent.

Record the decision and rationale in the relevant OpenSpec change or `docs/decisions/`. If unanswered, mark blocked; never silently choose a scientific value or architecture direction. For requested revisions after review, Lead reads `verification/owner-decision.json` on a later execution and resumes from durable feedback; no original Pi session or background listener is required.
