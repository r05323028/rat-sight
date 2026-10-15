# Design

## Context
The test fixture isolates one OpenSpec requirement from repository worktree state.

## Goals / Non-Goals

**Goals:** Exercise CLI and gate behavior.

**Non-Goals:** Model real scientific evidence or prove review independence.

## Decisions
Keep fixture paths and gate state static so tests mutate only the relevant decision.

## Risks / Trade-offs
Recorded test evidence is synthetic and proves no execution outside the test.
