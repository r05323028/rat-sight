from __future__ import annotations

import networkx as nx
import pytest
from ratsight_simulation.graph.network import create_synthetic_graph
from ratsight_simulation.movement.random_walk import (
    edge_transition_probabilities,
    run_weighted_random_walk,
)
from ratsight_simulation.validation.probability import probabilities_are_normalized


def test_synthetic_graph_has_simulated_provenance_and_positive_weights() -> None:
    graph = create_synthetic_graph()
    assert graph.graph["classification"] == "SIMULATED"
    assert graph.number_of_nodes() > 0 and graph.number_of_edges() > 0
    assert all(data["movement_weight"] > 0 for *_, data in graph.edges(data=True))


def test_transition_probabilities_are_normalized() -> None:
    graph = create_synthetic_graph()
    transitions = edge_transition_probabilities(graph, "n0")
    assert probabilities_are_normalized(item.probability for item in transitions)


def test_fixed_seed_reproduces_visit_counts_and_normalized_frequencies() -> None:
    graph = create_synthetic_graph()
    first = run_weighted_random_walk(graph, walkers=20, steps=10, seed=73)
    second = run_weighted_random_walk(graph, walkers=20, steps=10, seed=73)
    assert first == second
    assert sum(first.node_visits.values()) == 20 * 11
    assert sum(first.edge_visits.values()) == 20 * 10
    assert probabilities_are_normalized(first.node_probabilities.values())
    assert probabilities_are_normalized(first.edge_probabilities.values())


def test_time_dependent_edge_multipliers_change_transition_weights() -> None:
    graph = nx.MultiDiGraph()
    graph.add_edge("a", "b", edge_id="ab", movement_weight=1.0, time_multipliers=[1.0, 4.0])
    graph.add_edge("a", "c", edge_id="ac", movement_weight=1.0)
    at_zero = {
        item.target: item.probability for item in edge_transition_probabilities(graph, "a", step=0)
    }
    at_one = {
        item.target: item.probability for item in edge_transition_probabilities(graph, "a", step=1)
    }
    assert at_zero == {"b": 0.5, "c": 0.5}
    assert at_one == {"b": 0.8, "c": 0.2}


def test_missing_transitions_fail_explicitly() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("isolated")
    with pytest.raises(ValueError, match="no eligible outgoing edges"):
        edge_transition_probabilities(graph, "isolated")
