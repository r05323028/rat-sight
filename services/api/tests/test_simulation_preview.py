import pytest
from ratsight_api.api.schemas import SimulationPreviewRequest, SimulationPreviewResponse
from ratsight_api.application.simulation_preview import (
    UnknownOriginNodeError,
    preview_simulation,
)


def test_osm_is_default_study_area() -> None:
    assert SimulationPreviewRequest().study_area == "taipei_osm_songshan"


def test_default_preview_uses_the_pinned_osm_network() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(SimulationPreviewRequest(walkers=2, duration_steps=3))
    )
    assert response.parameters.study_area == "taipei_osm_songshan"
    assert response.provenance.source_type == "osm_surface_network"


def test_schematic_preview_does_not_load_osm_source(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_loaded() -> None:
        pytest.fail("explicit schematic preview must not load OSM source")

    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.load_osm_surface_graph",
        fail_if_loaded,
    )
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_synthetic_demo", walkers=2, duration_steps=3
            )
        )
    )
    assert response.parameters.study_area == "taipei_synthetic_demo"
    assert response.provenance.source_type == "synthetic_fixture"


def test_osm_preview_returns_simulated_geometry_and_trajectories() -> None:
    result = preview_simulation(
        SimulationPreviewRequest(study_area="taipei_osm_songshan", walkers=2, duration_steps=3)
    )
    response = SimulationPreviewResponse.model_validate(result)
    assert response.provenance.source_type == "osm_surface_network"
    assert (
        response.provenance.source_sha256
        == "faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e"
    )
    assert len(response.trajectories) == 2
    assert all(step.geometry for trajectory in response.trajectories for step in trajectory.edges)
    assert any(
        len(step.geometry) > 2 for trajectory in response.trajectories for step in trajectory.edges
    )


def test_default_origin_is_reported_as_a_default() -> None:
    result = preview_simulation(SimulationPreviewRequest(walkers=2, duration_steps=3))
    response = SimulationPreviewResponse.model_validate(result)
    assert response.origin.selection == "default"
    assert response.origin.classification == "SIMULATED"
    assert response.parameters.origin_node_id == response.origin.node_id
    assert response.origin.node_id in {node.id for node in response.nodes}


def test_identical_requests_are_reproducible() -> None:
    first = preview_simulation(SimulationPreviewRequest(walkers=2, duration_steps=3))
    second = preview_simulation(SimulationPreviewRequest(walkers=2, duration_steps=3))
    assert first["origin"] == second["origin"]
    assert first["trajectories"] == second["trajectories"]


def test_user_origin_starts_walks_there_and_is_echoed() -> None:
    default = SimulationPreviewResponse.model_validate(
        preview_simulation(SimulationPreviewRequest(walkers=2, duration_steps=3))
    )
    chosen = next(node.id for node in default.nodes if node.id != default.origin.node_id)
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(walkers=2, duration_steps=3, origin_node_id=chosen)
        )
    )
    assert response.origin.node_id == chosen
    assert response.origin.selection == "user"
    assert response.parameters.origin_node_id == chosen
    assert all(
        trajectory.edges[0].source == chosen
        for trajectory in response.trajectories
        if trajectory.edges
    )


def test_unknown_origin_node_is_rejected_instead_of_snapped() -> None:
    with pytest.raises(UnknownOriginNodeError):
        preview_simulation(SimulationPreviewRequest(origin_node_id="not-a-real-node"))


def test_trajectory_steps_carry_zero_based_step_index() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(SimulationPreviewRequest(walkers=2, duration_steps=3))
    )
    for trajectory in response.trajectories:
        assert [step.step_index for step in trajectory.edges] == list(range(len(trajectory.edges)))


def test_reachability_reports_directed_topology_from_the_origin() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(SimulationPreviewRequest(walkers=2, duration_steps=3))
    )
    reachability = response.reachability
    assert reachability.classification == "SIMULATED"
    assert reachability.origin_node_id == response.origin.node_id
    assert reachability.total_nodes == len(response.nodes)
    assert reachability.total_edges == len(response.edges)
    assert 0 < reachability.reachable_nodes <= reachability.total_nodes
    assert reachability.component_count >= 1
    assert "not habitat" in reachability.note


def test_reachability_follows_a_user_selected_origin() -> None:
    default = SimulationPreviewResponse.model_validate(
        preview_simulation(SimulationPreviewRequest(walkers=1, duration_steps=2))
    )
    chosen = next(node.id for node in default.nodes if node.id != default.origin.node_id)
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(walkers=1, duration_steps=2, origin_node_id=chosen)
        )
    )
    assert response.reachability.origin_node_id == chosen


def test_termination_reason_is_consistent_with_terminated_early() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(SimulationPreviewRequest(walkers=3, duration_steps=3))
    )
    for trajectory in response.trajectories:
        assert trajectory.termination_reason in {
            "completed",
            "dead_end",
            "no_eligible_transition",
        }
        assert trajectory.terminated_early is (trajectory.termination_reason != "completed")
