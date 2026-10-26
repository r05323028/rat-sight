# Proposal

## What Changes

Add the next bounded slice after the approved network MVP:

- expose and label deterministic simulation origin;
- add map origin selection from eligible network nodes;
- add client-side step playback over already returned trajectory edges;
- show current step, play/pause, previous/next, selected trajectory, and origin/termination semantics;
- preserve aggregate output, provenance, source boundaries, synthetic classifications, and bounded payloads.

## Why

The current network simulation uses arbitrary first-node origin and renders complete static paths. Municipal Analyst review found no way to inspect movement sequence over steps. Playback must represent a stepwise synthetic sequence, never elapsed time or observed animal movement.

## Scope

Minimal API additions for origin and step identity; frontend playback derived from completed response. No streaming, WebSockets, biological calibration, underground traversal, real observations, or risk model.

## Non-goals

No Taipei-wide graph, stormwater traversal, ML, population dynamics, real-time clock, or claim that unvisited areas are absent.
