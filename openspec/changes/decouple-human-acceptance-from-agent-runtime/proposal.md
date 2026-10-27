# Decouple human acceptance from agent runtime

## Why

RatSight currently treats OpenRig escalation and final owner acceptance as adjacent workflow concerns. Project owners need a local, durable way to review and decide on verified OpenSpec changes after agent execution ends, without weakening mandatory policy approvals or archive controls.

## What Changes

- Add local read-only review/status and interactive owner-decision commands.
- Store revision-bound owner decisions separately from policy approvals.
- Require current owner acceptance in the project archive wrapper.
- Document durable feedback and readiness boundaries.

## Scope

- Add a small standard-library local CLI for read-only change review/status and interactive owner decisions.
- Store revision-bound owner decisions separately from required policy approval records.
- Require current owner acceptance in the project archive wrapper.
- Document durable feedback and resume behavior for future Lead executions.

## Non-goals

No authentication service, database, background worker, OpenRig/TUI replacement, automatic acceptance, automatic archive, or historical-change migration.
