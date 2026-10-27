from typing import cast

import pytest
from ratsight_api.api.schemas import (
    CitizenReportCellPolygon,
    OriginSourceIdentity,
    SimulationPreviewRequest,
    SimulationPreviewResponse,
)
from ratsight_api.application.citizen_report_aggregates import (
    CitizenReportCellNotFound,
    CitizenReportOriginCell,
)
from ratsight_api.application.simulation_preview import (
    OriginCellResolutionError,
    UnknownOriginNodeError,
)
from ratsight_api.application.simulation_preview import (
    preview_simulation as _preview_simulation,
)
from ratsight_geo.osm import load_osm_surface_graph
from sqlalchemy.orm import Session

OSM_TEST_CELL_ID = "fixture:osm-origin"
OSM_ORIGIN_SOURCE = OriginSourceIdentity(
    dataset_id="ratdar-taipei-public-export",
    resource_version="2026-10-26T20:53:32Z",
    content_sha256="e" * 64,
)


def origin_cell(
    polygon: CitizenReportCellPolygon,
    *,
    feature_id: str = OSM_TEST_CELL_ID,
    report_type: str = "sighting",
) -> CitizenReportOriginCell:
    """Build the resolver result the application layer returns for one snapshot."""
    return CitizenReportOriginCell(
        feature_id=feature_id,
        polygon=polygon,
        dataset_id=OSM_ORIGIN_SOURCE.dataset_id,
        resource_version=OSM_ORIGIN_SOURCE.resource_version,
        content_sha256=OSM_ORIGIN_SOURCE.content_sha256,
        cell_id=feature_id.rsplit(":", 2)[0],
        month=feature_id.rsplit(":", 2)[1],
        report_type=report_type,
        report_type_eligible=True,
        report_type_reason="eligible_sighting_candidate",
        policy_version="origin-report-category-v1",
        cell_size_meters=250,
        source_url="https://ratdar.taipei/",
        attribution="fixture-only attribution",
    )


def preview_simulation(
    request: SimulationPreviewRequest, *, session: Session | None = None
) -> dict[str, object]:
    if request.study_area == "taipei_osm_songshan" and session is None:
        session = cast(Session, object())
    return _preview_simulation(request, session=session)


@pytest.fixture(autouse=True)
def _stub_osm_origin_cell(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = load_osm_surface_graph()
    isolated: tuple[float, float] | None = None
    for node_id, data in graph.nodes(data=True):
        lon, lat = data["coordinates"]
        if all(
            abs(other["coordinates"][0] - lon) > 5e-7 or abs(other["coordinates"][1] - lat) > 5e-7
            for other_id, other in graph.nodes(data=True)
            if other_id != node_id
        ):
            isolated = (lon, lat)
            break
    assert isolated is not None, "pinned OSM graph has no isolated node for the fixture"
    lon, lat = isolated
    half = 1e-7
    cell = CitizenReportCellPolygon(
        coordinates=[
            [
                [lon - half, lat - half],
                [lon - half, lat + half],
                [lon + half, lat + half],
                [lon + half, lat - half],
                [lon - half, lat - half],
            ]
        ]
    )
    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.get_citizen_report_origin_cell",
        lambda _session, _feature_id, _source: origin_cell(cell),
    )


def test_study_area_is_required() -> None:
    with pytest.raises(ValueError):
        SimulationPreviewRequest()  # pyright: ignore[reportCallIssue] -- assert required-field validation


def test_default_preview_uses_the_pinned_osm_network() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id=OSM_TEST_CELL_ID,
                origin_source=OSM_ORIGIN_SOURCE,
                walkers=2,
                duration_steps=3,
            )
        )
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
                study_area="taipei_synthetic_demo",
                origin_node_id="n0",
                walkers=2,
                duration_steps=3,
            )
        )
    )
    assert response.parameters.study_area == "taipei_synthetic_demo"
    assert response.provenance.source_type == "synthetic_fixture"


def test_osm_preview_returns_simulated_geometry_and_trajectories() -> None:
    result = preview_simulation(
        SimulationPreviewRequest(
            study_area="taipei_osm_songshan",
            origin_cell_id=OSM_TEST_CELL_ID,
            origin_source=OSM_ORIGIN_SOURCE,
            walkers=2,
            duration_steps=3,
        )
    )
    response = SimulationPreviewResponse.model_validate(result)
    assert response.provenance.source_type == "osm_surface_network"
    assert (
        response.provenance.source_sha256
        == "9db94dd723445fb45e73a77dca4ee4a74783af26e04794fc3fc9d5f63aa0f868"
    )
    assert len(response.trajectories) == 2
    assert all(step.geometry for trajectory in response.trajectories for step in trajectory.edges)
    assert any(
        len(step.geometry) > 2 for trajectory in response.trajectories for step in trajectory.edges
    )


def test_osm_origin_is_required_and_graph_nodes_are_rejected() -> None:
    with pytest.raises(ValueError, match="origin_cell_id is required"):
        SimulationPreviewRequest(study_area="taipei_osm_songshan")
    with pytest.raises(ValueError, match="origin_node_id is not accepted"):
        SimulationPreviewRequest(study_area="taipei_osm_songshan", origin_node_id="arbitrary-node")
    invalid = SimulationPreviewRequest.model_construct(
        study_area="taipei_osm_songshan", origin_node_id=None, origin_cell_id=None
    )
    with pytest.raises(OriginCellResolutionError, match="origin_cell_id is required"):
        _preview_simulation(invalid)


def test_identical_requests_are_reproducible() -> None:
    first = preview_simulation(
        SimulationPreviewRequest(
            study_area="taipei_osm_songshan",
            origin_cell_id=OSM_TEST_CELL_ID,
            origin_source=OSM_ORIGIN_SOURCE,
            walkers=2,
            duration_steps=3,
        )
    )
    second = preview_simulation(
        SimulationPreviewRequest(
            study_area="taipei_osm_songshan",
            origin_cell_id=OSM_TEST_CELL_ID,
            origin_source=OSM_ORIGIN_SOURCE,
            walkers=2,
            duration_steps=3,
        )
    )
    assert first["origin"] == second["origin"]
    assert first["trajectories"] == second["trajectories"]


def test_cell_origin_starts_walkers_at_resolved_node_and_is_echoed() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id=OSM_TEST_CELL_ID,
                origin_source=OSM_ORIGIN_SOURCE,
                walkers=2,
                duration_steps=3,
            )
        )
    )
    assert response.origin.selection == "cell"
    assert response.origin.cell_id == OSM_TEST_CELL_ID
    assert response.parameters.origin_cell_id == OSM_TEST_CELL_ID
    assert all(
        trajectory.edges[0].source in response.origin.node_ids
        for trajectory in response.trajectories
        if trajectory.edges
    )


def test_synthetic_origin_cell_resolves_and_stays_distinct_from_node() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_synthetic_demo",
                origin_cell_id="synthetic-cell-n0",
                walkers=2,
                duration_steps=3,
            )
        )
    )
    assert response.origin.selection == "cell"
    assert response.origin.cell_id == "synthetic-cell-n0"
    assert response.origin.node_id == "n0"
    assert response.parameters.origin_cell_id == "synthetic-cell-n0"
    assert response.provenance.source_crs == "EPSG:4326"


def test_real_origin_cell_requires_database_access() -> None:
    with pytest.raises(OriginCellResolutionError, match="require database access"):
        _preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id="synthetic-cell-n0",
                origin_source=OSM_ORIGIN_SOURCE,
            )
        )


def test_real_origin_cell_resolves_one_strictly_contained_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = load_osm_surface_graph()
    isolated: tuple[str, float, float] | None = None
    for node_id, data in graph.nodes(data=True):
        lon, lat = data["coordinates"]
        if all(
            abs(other["coordinates"][0] - lon) > 5e-7 or abs(other["coordinates"][1] - lat) > 5e-7
            for other_id, other in graph.nodes(data=True)
            if other_id != node_id
        ):
            isolated = (str(node_id), lon, lat)
            break
    assert isolated is not None, "pinned OSM graph has no isolated node for this test"
    node_id, lon, lat = isolated
    half = 1e-7
    cell = CitizenReportCellPolygon(
        coordinates=[
            [
                [lon - half, lat - half],
                [lon - half, lat + half],
                [lon + half, lat + half],
                [lon + half, lat - half],
                [lon - half, lat - half],
            ]
        ]
    )
    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.get_citizen_report_origin_cell",
        lambda _session, feature_id, _source: origin_cell(cell, feature_id=feature_id),
    )
    feature_id = "g250m:1:2:2026-05:sighting"
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id=feature_id,
                origin_source=OSM_ORIGIN_SOURCE,
                walkers=2,
                duration_steps=3,
            ),
            session=cast(Session, object()),
        )
    )
    assert response.origin.selection == "cell"
    assert response.origin.cell_id == feature_id
    assert response.origin.node_id == node_id
    assert response.origin.node_ids == [node_id]
    assert response.origin.cell_candidate_count == 1
    assert response.origin.cell_resolver_version == "strict-in-cell-v1"
    assert response.origin.source_data_class == "CITIZEN_REPORT_AGGREGATE"
    assert response.origin.source_classification == "UNVERIFIED"
    assert response.origin.source_kind == "public_citizen_report_export"
    assert "one strictly in-cell graph node" in response.origin.note
    assert "UNVERIFIED" in response.origin.note
    assert any("suppressed aggregate of UNVERIFIED" in item for item in response.assumptions)
    assert response.parameters.origin_cell_id == feature_id
    assert response.parameters.origin_node_ids == [node_id]
    assert response.reachability.origin_node_ids == [node_id]


def test_synthetic_aggregate_origin_remains_simulated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = load_osm_surface_graph()
    isolated: tuple[float, float] | None = None
    for node_id, data in graph.nodes(data=True):
        lon, lat = data["coordinates"]
        if all(
            abs(other["coordinates"][0] - lon) > 5e-7 or abs(other["coordinates"][1] - lat) > 5e-7
            for other_id, other in graph.nodes(data=True)
            if other_id != node_id
        ):
            isolated = (lon, lat)
            break
    assert isolated is not None
    lon, lat = isolated
    half = 1e-7
    fixture_cell = CitizenReportCellPolygon(
        coordinates=[
            [
                [lon - half, lat - half],
                [lon - half, lat + half],
                [lon + half, lat + half],
                [lon + half, lat - half],
                [lon - half, lat - half],
            ]
        ],
        data_class="SYNTHETIC_AGGREGATE_FIXTURE",
        classification="SIMULATED",
        source_kind="synthetic_aggregate_fixture",
    )
    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.get_citizen_report_origin_cell",
        lambda _session, feature_id, _source: origin_cell(fixture_cell, feature_id=feature_id),
    )
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id="ratsight-smoke-fixture:2026-05:sighting",
                origin_source=OSM_ORIGIN_SOURCE,
                walkers=1,
                duration_steps=1,
            )
        )
    )
    assert response.origin.source_data_class == "SYNTHETIC_AGGREGATE_FIXTURE"
    assert response.origin.source_classification == "SIMULATED"
    assert response.origin.source_kind == "synthetic_aggregate_fixture"
    assert "SIMULATED aggregate test fixture" in response.origin.note
    assert "UNVERIFIED" not in response.origin.note
    assert any("SIMULATED smoke-test fixture" in item for item in response.assumptions)


def test_real_origin_cell_seeds_every_in_cell_node(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = load_osm_surface_graph()
    # A published 250 m cell near Songshan: bounded enough to keep the response small, but with
    # several in-cell graph nodes so the uniform multi-origin path is exercised.
    west, south, east, north = (
        121.54306283616624,
        25.031440891124685,
        121.54554143524115,
        25.033686669062163,
    )
    expected_nodes = sorted(
        str(node)
        for node, data in graph.nodes(data=True)
        if west <= float(data["coordinates"][0]) <= east
        and south <= float(data["coordinates"][1]) <= north
    )
    assert len(expected_nodes) > 1
    cell = CitizenReportCellPolygon(
        coordinates=[
            [
                [west, south],
                [west, north],
                [east, north],
                [east, south],
                [west, south],
            ]
        ]
    )
    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.get_citizen_report_origin_cell",
        lambda _session, feature_id, _source: origin_cell(cell, feature_id=feature_id),
    )
    feature_id = "g250m:11146:49037:2026-05:sighting"
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id=feature_id,
                origin_source=OSM_ORIGIN_SOURCE,
                walkers=5,
                duration_steps=3,
            ),
            session=cast(Session, object()),
        )
    )
    assert response.origin.selection == "cell"
    assert response.origin.cell_id == feature_id
    assert response.origin.node_id == expected_nodes[0]
    assert response.origin.node_ids == expected_nodes
    assert response.origin.cell_candidate_count == len(expected_nodes)
    assert response.origin.cell_resolver_version == "uniform-in-cell-v1"
    assert "uniformly" in response.origin.note
    assert "UNVERIFIED" in response.origin.note
    assert any("walkers start uniformly" in item for item in response.assumptions)
    assert response.parameters.origin_node_ids == expected_nodes
    assert response.reachability.origin_node_ids == expected_nodes
    assert 0 < response.reachability.reachable_nodes <= response.reachability.total_nodes
    assert response.visualization.mode == "local_reference"
    assert response.visualization.total_nodes == graph.number_of_nodes()
    assert response.visualization.returned_nodes == len(response.nodes)
    assert response.visualization.returned_edges == len(response.edges)
    assert response.visualization.returned_nodes < response.visualization.total_nodes
    assert response.reachability.sampled_nodes > 0
    first_sources = {
        trajectory.edges[0].source for trajectory in response.trajectories if trajectory.edges
    }
    assert first_sources <= set(expected_nodes)


def test_missing_real_origin_cell_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_cell(
        _session: object, _feature_id: str, _source: OriginSourceIdentity
    ) -> CitizenReportOriginCell:
        raise CitizenReportCellNotFound("origin cell is not present in the selected snapshot")

    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.get_citizen_report_origin_cell",
        missing_cell,
    )
    with pytest.raises(OriginCellResolutionError, match="not present"):
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id="g250m:1:2:2026-05:sighting",
                origin_source=OSM_ORIGIN_SOURCE,
            ),
            session=cast(Session, object()),
        )


def test_real_origin_cell_without_an_in_cell_node_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty_cell = CitizenReportCellPolygon(
        coordinates=[[[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [0.0, 0.0]]]
    )
    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.get_citizen_report_origin_cell",
        lambda _session, feature_id, _source: origin_cell(empty_cell, feature_id=feature_id),
    )
    with pytest.raises(OriginCellResolutionError, match="0 eligible graph nodes"):
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id="g250m:1:2:2026-05:sighting",
                origin_source=OSM_ORIGIN_SOURCE,
            ),
            session=cast(Session, object()),
        )


def test_unknown_synthetic_origin_cell_is_rejected_instead_of_mapped() -> None:
    with pytest.raises(OriginCellResolutionError, match="bounded synthetic"):
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_synthetic_demo", origin_cell_id="ratdar-cell-123"
            )
        )


def test_cell_and_node_origins_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_synthetic_demo",
                origin_cell_id="synthetic-cell-n0",
                origin_node_id="n0",
            )
        )


def test_unknown_origin_node_is_rejected_instead_of_snapped() -> None:
    with pytest.raises(UnknownOriginNodeError):
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_synthetic_demo", origin_node_id="not-a-real-node"
            )
        )


def test_trajectory_steps_carry_zero_based_step_index() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id=OSM_TEST_CELL_ID,
                origin_source=OSM_ORIGIN_SOURCE,
                walkers=2,
                duration_steps=3,
            )
        )
    )
    for trajectory in response.trajectories:
        assert [step.step_index for step in trajectory.edges] == list(range(len(trajectory.edges)))


def test_reachability_reports_directed_topology_from_the_origin() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id=OSM_TEST_CELL_ID,
                origin_source=OSM_ORIGIN_SOURCE,
                walkers=2,
                duration_steps=3,
            )
        )
    )
    reachability = response.reachability
    assert reachability.classification == "SIMULATED"
    assert reachability.origin_node_id == response.origin.node_id
    assert response.visualization.mode == "local_reference"
    assert response.visualization.radius_meters == 750.0
    assert response.visualization.returned_nodes == len(response.nodes)
    assert response.visualization.returned_edges == len(response.edges)
    assert reachability.total_nodes == response.visualization.total_nodes
    assert reachability.total_edges == response.visualization.total_edges
    assert reachability.total_nodes > len(response.nodes)
    assert reachability.total_edges > len(response.edges)
    assert 0 < reachability.reachable_nodes <= reachability.total_nodes
    assert reachability.sampled_nodes >= 1
    assert reachability.component_count >= 1
    assert "not habitat" in reachability.note


def test_reachability_follows_an_explicit_synthetic_origin() -> None:
    chosen = "n2"
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_synthetic_demo",
                origin_node_id=chosen,
                walkers=1,
                duration_steps=2,
            )
        )
    )
    assert response.reachability.origin_node_id == chosen


def test_termination_reason_is_consistent_with_terminated_early() -> None:
    response = SimulationPreviewResponse.model_validate(
        preview_simulation(
            SimulationPreviewRequest(
                study_area="taipei_osm_songshan",
                origin_cell_id=OSM_TEST_CELL_ID,
                origin_source=OSM_ORIGIN_SOURCE,
                walkers=3,
                duration_steps=3,
            )
        )
    )
    for trajectory in response.trajectories:
        assert trajectory.termination_reason in {
            "completed",
            "dead_end",
            "no_eligible_transition",
        }
        assert trajectory.terminated_early is (trajectory.termination_reason != "completed")
