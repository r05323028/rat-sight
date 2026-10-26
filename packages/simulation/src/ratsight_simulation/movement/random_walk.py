"""Reproducible weighted random walks over directed multilayer graphs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

import networkx as nx
import numpy as np

from ratsight_simulation.behavior.constraints import EdgeConstraint


class NoEligibleTransitionError(ValueError):
    """No outgoing edge satisfies current constraints."""


@dataclass(frozen=True)
class Transition:
    source: str
    target: str
    edge_id: str
    weight: float
    probability: float


@dataclass(frozen=True)
class VisitStatistics:
    node_visits: dict[str, int]
    edge_visits: dict[tuple[str, str, str], int]
    node_probabilities: dict[str, float]
    edge_probabilities: dict[tuple[str, str, str], float]
    trajectories: list[list[tuple[str, str, str]]]
    terminated_early: list[bool]


def edge_transition_probabilities(
    graph: nx.MultiDiGraph,
    node: str,
    *,
    step: int = 0,
    constraints: Sequence[EdgeConstraint] = (),
) -> list[Transition]:
    """Normalize positive movement weights after optional time/behavior constraints."""
    candidates: list[tuple[str, str, str, float]] = []
    for _, target, key, attributes in sorted(
        graph.out_edges(node, keys=True, data=True),
        key=lambda edge: (str(edge[1]), str(edge[2])),
    ):
        if any(
            not constraint.allows(node, str(target), attributes, step) for constraint in constraints
        ):
            continue
        weight = float(attributes.get("movement_weight", 1.0))
        multipliers = attributes.get("time_multipliers")
        if multipliers:
            multiplier = float(multipliers[step % len(multipliers)])
            weight *= multiplier
        if not isfinite(weight) or weight <= 0:
            raise ValueError("eligible edge movement weights must be finite and positive")
        candidates.append((node, str(target), str(attributes.get("edge_id", key)), weight))
    if not candidates:
        raise NoEligibleTransitionError(f"node {node!r} has no eligible outgoing edges")
    weights = np.asarray([candidate[3] for candidate in candidates], dtype=float)
    probabilities = weights / weights.sum()
    return [
        Transition(source, target, edge_id, weight, float(probability))
        for (source, target, edge_id, weight), probability in zip(
            candidates, probabilities, strict=True
        )
    ]


def run_weighted_random_walk(
    graph: nx.MultiDiGraph,
    *,
    walkers: int = 24,
    steps: int = 12,
    seed: int = 42,
    start_node: str = "n0",
) -> VisitStatistics:
    """Run Monte Carlo walks; equal graph, parameters and seed yield equal counts."""
    if walkers < 1 or steps < 1 or seed < 0:
        raise ValueError("walkers and steps must be positive and seed must be non-negative")
    if start_node not in graph:
        raise ValueError(f"start node {start_node!r} is not in graph")
    random = np.random.default_rng(seed)
    node_visits = {str(node): 0 for node in graph.nodes}
    edge_visits: dict[tuple[str, str, str], int] = {}
    trajectories: list[list[tuple[str, str, str]]] = []
    terminated_early: list[bool] = []
    for source, target, key, attributes in graph.edges(keys=True, data=True):
        edge_key = (str(source), str(target), str(attributes.get("edge_id", key)))
        edge_visits[edge_key] = 0
    for _ in range(walkers):
        current = start_node
        node_visits[current] += 1
        trajectory: list[tuple[str, str, str]] = []
        trajectories.append(trajectory)
        stopped = False
        for step in range(steps):
            if graph.out_degree(current) == 0:
                stopped = True
                break
            try:
                transitions = edge_transition_probabilities(graph, current, step=step)
            except NoEligibleTransitionError:
                stopped = True
                break
            selected = transitions[
                int(random.choice(len(transitions), p=[t.probability for t in transitions]))
            ]
            edge_key = (selected.source, selected.target, selected.edge_id)
            edge_visits[edge_key] += 1
            trajectory.append(edge_key)
            current = selected.target
            node_visits[current] += 1
        terminated_early.append(stopped)
    total_node_visits = sum(node_visits.values())
    total_edge_visits = sum(edge_visits.values())
    return VisitStatistics(
        node_visits=node_visits,
        edge_visits=edge_visits,
        node_probabilities={node: count / total_node_visits for node, count in node_visits.items()},
        edge_probabilities={
            edge: count / total_edge_visits if total_edge_visits else 0.0
            for edge, count in edge_visits.items()
        },
        trajectories=trajectories,
        terminated_early=terminated_early,
    )
