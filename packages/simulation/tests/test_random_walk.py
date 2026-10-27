from __future__ import annotations

import networkx as nx
import pytest
from ratsight_simulation.graph.network import (
    create_synthetic_graph,
    reachability_summary,
    resolve_origin_cell,
)
from ratsight_simulation.movement.random_walk import (
    edge_transition_probabilities,
    run_weighted_random_walk,
)
from ratsight_simulation.validation.probability import probabilities_are_normalized


def test_origin_cell_resolves_only_strictly_in_cell_node() -> None:
    graph = create_synthetic_graph()
    result = resolve_origin_cell(
        graph,
        "cell-n0",
        [
            (121.529, 25.039),
            (121.531, 25.039),
            (121.531, 25.041),
            (121.529, 25.041),
            (121.529, 25.039),
        ],
    )
    assert result["origin_node_id"] == "n0"
    assert result["origin_node_ids"] == ["n0"]
    assert result["candidate_count"] == 1
    assert result["resolver_version"] == "strict-in-cell-v1"
    assert result["classification"] == "UNVERIFIED"


def test_origin_cell_resolution_is_deterministic() -> None:
    polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]
    node_orders = [[("inside", (0.5, 0.5)), ("outside", (2.0, 2.0))]]
    node_orders.append(list(reversed(node_orders[0])))
    results = []
    for node_order in node_orders:
        graph = nx.MultiDiGraph()
        for node_id, coordinates in node_order:
            graph.add_node(node_id, coordinates=coordinates)
        results.append(resolve_origin_cell(graph, "fixture", polygon))

    assert results[0] == results[1]


def test_origin_cell_rejects_unclosed_polygon() -> None:
    graph = nx.MultiDiGraph()
    with pytest.raises(ValueError, match="closed and contain at least four points"):
        resolve_origin_cell(
            graph,
            "open-ring",
            [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        )


def test_origin_cell_rejects_boundary_candidate() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("boundary", coordinates=(0.0, 0.5))
    polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]

    with pytest.raises(ValueError, match="0 eligible"):
        resolve_origin_cell(graph, "boundary", polygon)


def test_origin_cell_rejects_no_candidate() -> None:
    graph = create_synthetic_graph()
    with pytest.raises(ValueError, match="0 eligible"):
        resolve_origin_cell(
            graph,
            "empty",
            [
                (121.0, 25.0),
                (121.001, 25.0),
                (121.001, 25.001),
                (121.0, 25.001),
                (121.0, 25.0),
            ],
        )


def test_origin_cell_resolves_all_in_cell_nodes_uniformly() -> None:
    graph = create_synthetic_graph()
    result = resolve_origin_cell(
        graph,
        "multi",
        [
            (121.529, 25.039),
            (121.541, 25.039),
            (121.541, 25.046),
            (121.529, 25.046),
            (121.529, 25.039),
        ],
    )
    assert result["origin_node_id"] == "n0"
    assert result["origin_node_ids"] == ["n0", "n1"]
    assert result["candidate_count"] == 2
    assert result["resolver_version"] == "uniform-in-cell-v1"
    assert result["classification"] == "UNVERIFIED"


def test_uniform_multi_start_uses_only_requested_nodes_and_is_reproducible() -> None:
    graph = create_synthetic_graph()
    first = run_weighted_random_walk(graph, walkers=20, steps=2, seed=7, start_nodes=["n0", "n1"])
    second = run_weighted_random_walk(graph, walkers=20, steps=2, seed=7, start_nodes=["n0", "n1"])
    assert first.trajectories == second.trajectories
    assert first.node_visits == second.node_visits
    first_sources = {trajectory[0][0] for trajectory in first.trajectories if trajectory}
    assert first_sources == {"n0", "n1"}
    assert first.node_visits["n0"] + first.node_visits["n1"] >= 20
    with pytest.raises(ValueError, match="at least one node"):
        run_weighted_random_walk(graph, walkers=1, steps=1, start_nodes=[])
    with pytest.raises(ValueError, match="not in graph"):
        run_weighted_random_walk(graph, walkers=1, steps=1, start_nodes=["missing"])


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


def test_dead_end_terminates_walk_at_sink() -> None:
    graph = nx.MultiDiGraph()
    graph.add_edge("start", "sink", edge_id="start-sink", movement_weight=1.0)

    result = run_weighted_random_walk(graph, walkers=1, steps=4, seed=0, start_node="start")

    assert result.trajectories == [[("start", "sink", "start-sink")]]
    assert result.terminated_early == [True]
    assert result.node_visits == {"start": 1, "sink": 1}


def test_isolated_origin_returns_empty_trajectory() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("origin")

    result = run_weighted_random_walk(graph, walkers=1, steps=4, seed=0, start_node="origin")

    assert result.trajectories == [[]]
    assert result.terminated_early == [True]
    assert result.node_visits == {"origin": 1}
    assert result.node_probabilities == {"origin": 1.0}
    assert result.edge_visits == {}
    assert result.edge_probabilities == {}


def test_termination_reasons_distinguish_completed_dead_end_and_eligibility() -> None:
    completed = run_weighted_random_walk(
        create_synthetic_graph(), walkers=2, steps=4, seed=11, start_node="n0"
    )
    assert completed.termination_reasons == ["completed", "completed"]
    assert completed.terminated_early == [False, False]

    dead_end_graph = nx.MultiDiGraph()
    dead_end_graph.add_edge("start", "sink", edge_id="start-sink", movement_weight=1.0)
    dead_end = run_weighted_random_walk(
        dead_end_graph, walkers=1, steps=4, seed=0, start_node="start"
    )
    assert dead_end.termination_reasons == ["dead_end"]

    class BlocksEverything:
        def allows(self, source, target, edge, step) -> bool:
            _ = (source, target, edge, step)
            return False

    blocked = run_weighted_random_walk(
        create_synthetic_graph(),
        walkers=1,
        steps=4,
        seed=0,
        start_node="n0",
        constraints=[BlocksEverything()],
    )
    assert blocked.termination_reasons == ["no_eligible_transition"]
    assert blocked.trajectories == [[]]


def test_reachability_summary_counts_directed_reachable_topology() -> None:
    graph = nx.MultiDiGraph()
    graph.add_edge("a", "b", edge_id="ab", movement_weight=1.0)
    graph.add_edge("b", "c", edge_id="bc", movement_weight=1.0)
    graph.add_node("island")

    summary = reachability_summary(graph, "a")

    assert summary == {
        "origin_node_id": "a",
        "origin_node_ids": ["a"],
        "reachable_nodes": 3,
        "total_nodes": 4,
        "reachable_edges": 2,
        "total_edges": 2,
        "component_count": 2,
    }
    union = reachability_summary(graph, ["a", "island"])
    assert union["origin_node_ids"] == ["a", "island"]
    assert union["reachable_nodes"] == 4
    assert union["reachable_edges"] == 2
    with pytest.raises(ValueError, match="not in graph"):
        reachability_summary(graph, ["a", "missing"])
    with pytest.raises(ValueError, match="at least one origin"):
        reachability_summary(graph, [])


def test_synthetic_graph_is_fully_reachable_from_every_node() -> None:
    graph = create_synthetic_graph()
    for node in graph.nodes:
        summary = reachability_summary(graph, node)
        assert summary["reachable_nodes"] == summary["total_nodes"]
        assert summary["component_count"] == 1
