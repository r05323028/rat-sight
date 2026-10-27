from math import cos, hypot, radians
from typing import cast

import networkx as nx
from ratsight_api.api.schemas import SimulationPreviewRequest
from ratsight_api.application.citizen_report_aggregates import (
    CitizenReportCellNotFound,
    CitizenReportDataError,
    CitizenReportQueryError,
    CitizenReportStorageError,
    get_citizen_report_cell_polygon,
)
from ratsight_geo.osm import load_osm_surface_graph
from ratsight_simulation.graph.network import (
    SYNTHETIC_FIXTURE_ID,
    create_synthetic_graph,
    reachability_summary,
    resolve_origin_cell,
)
from ratsight_simulation.models.metadata import MODEL_ID, MODEL_VERSION
from ratsight_simulation.movement.random_walk import run_weighted_random_walk
from sqlalchemy.orm import Session

VISUALIZATION_RADIUS_METERS = 750.0

COMMON_ASSUMPTIONS = [
    (
        "All movement weights are unitless hypothetical placeholders, not calibrated "
        "biological parameters."
    ),
    (
        "Every result is SIMULATED; no observation, hotspot, risk, prevalence, movement, "
        "or intervention claim is supported."
    ),
]
OSM_ASSUMPTIONS = COMMON_ASSUMPTIONS + [
    (
        "The OSM graph is surface-only; connectivity comes only from shared OSM way "
        "nodes; underground geometry is excluded."
    ),
    (
        "OSM data is © OpenStreetMap contributors and licensed under ODbL 1.0; source "
        "geometry is not biological evidence."
    ),
    (
        "Returned map nodes and edges are a local reference subset containing every origin "
        "node, displayed trajectory nodes, and nodes within 750 m of the representative "
        "origin; simulation and reachability totals use the full pinned graph."
    ),
]
SYNTHETIC_ASSUMPTIONS = COMMON_ASSUMPTIONS + [
    (
        "Graph topology and coordinates are schematic synthetic fixtures, not surveyed "
        "infrastructure or animal observations."
    ),
]


def _geometry(graph, source: str, target: str, edge_id: str) -> list[tuple[float, float]]:
    for _, candidate, key, attributes in graph.out_edges(source, keys=True, data=True):
        if str(candidate) == target and str(attributes.get("edge_id", key)) == edge_id:
            return list(
                attributes.get(
                    "geometry",
                    (graph.nodes[source]["coordinates"], graph.nodes[target]["coordinates"]),
                )
            )
    raise KeyError(f"edge not found: {source}->{target} {edge_id}")


class UnknownOriginNodeError(LookupError):
    """Requested origin_node_id is not a node of the selected study-area graph."""


class OriginCellResolutionError(ValueError):
    """Requested origin cell is unavailable or contains no eligible graph node."""


class OriginCellStorageError(RuntimeError):
    """Citizen-report aggregate storage could not resolve an origin cell."""


def _distance_meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Approximate local distance; only used to bound the map reference subset."""
    mean_latitude = radians((a[1] + b[1]) / 2.0)
    return hypot(
        (a[0] - b[0]) * 111_320.0 * cos(mean_latitude),
        (a[1] - b[1]) * 111_320.0,
    )


def _visualization_node_ids(
    graph: nx.MultiDiGraph,
    origins: list[str],
    trajectories: list[list[tuple[str, str, str]]],
) -> set[str]:
    """Keep origins, displayed trajectories, and a local ring for map legibility."""
    keep = set(origins)
    origin_coordinates = graph.nodes[origins[0]]["coordinates"]
    center = (float(origin_coordinates[0]), float(origin_coordinates[1]))
    for node_id, data in graph.nodes(data=True):
        coordinates = data["coordinates"]
        if _distance_meters(center, (float(coordinates[0]), float(coordinates[1]))) <= (
            VISUALIZATION_RADIUS_METERS
        ):
            keep.add(str(node_id))
    for trajectory in trajectories:
        for source, target, _ in trajectory:
            keep.add(source)
            keep.add(target)
    return keep


SYNTHETIC_ORIGIN_CELLS = {
    "synthetic-cell-n0": [
        (121.529, 25.039),
        (121.531, 25.039),
        (121.531, 25.041),
        (121.529, 25.041),
        (121.529, 25.039),
    ]
}


def preview_simulation(
    request: SimulationPreviewRequest, *, session: Session | None = None
) -> dict[str, object]:
    osm = request.study_area == "taipei_osm_songshan"
    graph = load_osm_surface_graph() if osm else create_synthetic_graph()
    # Resolve by exact IDs; never snap an unknown node or cell to another origin.
    node_by_id = {str(node_id): node_id for node_id in graph.nodes}
    requested_origin = request.origin_node_id
    if requested_origin is not None and request.origin_cell_id is not None:
        raise OriginCellResolutionError("origin_node_id and origin_cell_id are mutually exclusive")
    resolved_cell: dict[str, object] | None = None
    requested_origins: list[str] | None = None
    if request.origin_cell_id is not None:
        if osm:
            if session is None:
                raise OriginCellResolutionError(
                    "real citizen-report origin cells require database access"
                )
            try:
                stored = get_citizen_report_cell_polygon(session, request.origin_cell_id)
            except CitizenReportStorageError as exc:
                raise OriginCellStorageError(str(exc)) from exc
            except (
                CitizenReportCellNotFound,
                CitizenReportDataError,
                CitizenReportQueryError,
            ) as exc:
                raise OriginCellResolutionError(str(exc)) from exc
            polygon = [(float(x), float(y)) for x, y in stored.coordinates[0]]
        else:
            polygon = SYNTHETIC_ORIGIN_CELLS.get(request.origin_cell_id)
            if polygon is None:
                raise OriginCellResolutionError(
                    "origin_cell_id is enabled only for the bounded synthetic resolver fixture"
                )
        try:
            resolved_cell = resolve_origin_cell(graph, request.origin_cell_id, polygon)
        except ValueError as exc:
            raise OriginCellResolutionError(str(exc)) from exc
        requested_origins = [
            str(node) for node in cast(list[str], resolved_cell["origin_node_ids"])
        ]
        requested_origin = requested_origins[0]
    elif requested_origin is not None:
        requested_origins = [requested_origin]
    if requested_origin is not None and requested_origin not in node_by_id:
        raise UnknownOriginNodeError(
            f"origin_node_id {requested_origin!r} is not a node in "
            f"study area {request.study_area!r}"
        )
    if requested_origins is not None:
        unknown = [node for node in requested_origins if node not in node_by_id]
        if unknown:
            raise UnknownOriginNodeError(
                f"origin nodes {unknown!r} are not nodes in study area {request.study_area!r}"
            )
    start_node = (
        node_by_id[requested_origin] if requested_origin is not None else next(iter(graph.nodes))
    )
    walk_start_nodes = (
        requested_origins if requested_origins is not None and len(requested_origins) > 1 else None
    )
    statistics = run_weighted_random_walk(
        graph,
        walkers=request.walkers,
        steps=request.duration_steps,
        seed=request.random_seed,
        start_node=start_node,
        start_nodes=walk_start_nodes,
    )
    visible_trajectories = statistics.trajectories[:100]
    visible_origins = requested_origins if requested_origins is not None else [str(start_node)]
    visible_node_ids = (
        _visualization_node_ids(graph, visible_origins, visible_trajectories) if osm else None
    )
    node_ids = sorted(visible_node_ids) if visible_node_ids is not None else list(graph.nodes)
    edge_source = graph if visible_node_ids is None else graph.subgraph(visible_node_ids)
    nodes = [
        {
            "id": str(node_id),
            "coordinates": graph.nodes[node_id]["coordinates"],
            "visits": statistics.node_visits[str(node_id)],
            "probability": statistics.node_probabilities[str(node_id)],
            "classification": "SIMULATED",
        }
        for node_id in node_ids
    ]
    edges = []
    for source, target, key, attributes in edge_source.edges(keys=True, data=True):
        edge_id = str(attributes.get("edge_id", key))
        edge = {
            "source": str(source),
            "target": str(target),
            "edge_id": edge_id,
            "source_id": attributes.get("source_id"),
            "geometry": (
                {"type": "LineString", "coordinates": list(attributes["geometry"])}
                if attributes.get("geometry")
                else None
            ),
            "movement_weight": float(attributes["movement_weight"]),
            "visits": statistics.edge_visits[(str(source), str(target), edge_id)],
            "probability": statistics.edge_probabilities[(str(source), str(target), edge_id)],
            "classification": "SIMULATED",
        }
        edges.append(edge)
    trajectories = [
        {
            "walker_id": walker_id,
            "edges": [
                {
                    "step_index": step_index,
                    "source": source,
                    "target": target,
                    "edge_id": edge_id,
                    "geometry": _geometry(graph, source, target, edge_id),
                    "classification": "SIMULATED",
                }
                for step_index, (source, target, edge_id) in enumerate(trajectory)
            ],
            "terminated_early": statistics.terminated_early[walker_id],
            "termination_reason": statistics.termination_reasons[walker_id],
            "classification": "SIMULATED",
        }
        for walker_id, trajectory in enumerate(visible_trajectories)
    ]
    sampled_nodes = sum(1 for visits in statistics.node_visits.values() if visits > 0)
    return {
        "simulation_status": "completed",
        "classification": "SIMULATED",
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "origin": {
            "node_id": str(start_node),
            "node_ids": requested_origins if requested_origins is not None else [str(start_node)],
            "coordinates": tuple(graph.nodes[start_node]["coordinates"]),
            "selection": (
                "cell" if resolved_cell else ("user" if requested_origin is not None else "default")
            ),
            "cell_id": request.origin_cell_id,
            "cell_candidate_count": (resolved_cell["candidate_count"] if resolved_cell else None),
            "cell_resolver_version": (resolved_cell["resolver_version"] if resolved_cell else None),
            "classification": "SIMULATED",
            "note": (
                (
                    "Citizen-report aggregate cell input is UNVERIFIED; one strictly in-cell "
                    "graph node seeds the walkers. Movement output is SIMULATED and is not an "
                    "observed animal origin or migration."
                    if resolved_cell["candidate_count"] == 1
                    else f"Citizen-report aggregate cell input is UNVERIFIED; "
                    f"{resolved_cell['candidate_count']} eligible in-cell graph nodes seed "
                    "walkers uniformly; the marker is the first sorted node. Movement output "
                    "is SIMULATED and is not an observed animal origin or migration."
                )
                if osm and resolved_cell
                else "Synthetic model input; not an observed or reported animal origin."
            ),
        },
        "reachability": {
            **reachability_summary(
                graph,
                requested_origins if requested_origins is not None else start_node,
            ),
            "sampled_nodes": sampled_nodes,
            "classification": "SIMULATED",
            "note": (
                "Directed graph topology from the resolved origin over the full model graph; "
                "it is not habitat, food, sewer, or movement evidence."
            ),
        },
        "visualization": {
            "mode": "local_reference" if osm else "full_graph",
            "radius_meters": VISUALIZATION_RADIUS_METERS if osm else None,
            "returned_nodes": len(nodes),
            "returned_edges": len(edges),
            "total_nodes": int(graph.number_of_nodes()),
            "total_edges": int(graph.number_of_edges()),
            "note": (
                "Map nodes and edges are a local reference subset: all origin nodes, all "
                "displayed trajectory nodes, and nodes within 750 m of the representative "
                "origin, plus edges between included nodes. Reachability and simulation "
                "totals cover the full pinned graph."
                if osm
                else "Map nodes and edges cover the full schematic fixture graph."
            ),
        },
        "parameters": {
            "study_area": request.study_area,
            "origin_node_id": str(start_node),
            "origin_node_ids": (
                requested_origins if requested_origins is not None else [str(start_node)]
            ),
            "origin_cell_id": request.origin_cell_id,
            "duration_steps": request.duration_steps,
            "walkers": request.walkers,
            "random_seed": request.random_seed,
            "movement_model": request.movement_model,
            "intervention_scenario": request.intervention_scenario,
        },
        "provenance": {
            "classification": "SIMULATED",
            "source_type": "osm_surface_network" if osm else "synthetic_fixture",
            "source_id": graph.graph.get("source_id", SYNTHETIC_FIXTURE_ID),
            "source_crs": "EPSG:4326",
            "source_sha256": graph.graph.get("source_sha256"),
            "source_url": graph.graph.get("source_url"),
            "resource_version": graph.graph.get("resource_version"),
            "license": graph.graph.get("license"),
            "attribution": ("© OpenStreetMap contributors; ODbL 1.0" if osm else None),
            "coverage": graph.graph.get("coverage"),
            "note": (
                "Pinned external OSM surface fixture; shared OSM nodes only, geometry preserved; "
                "not animal observations."
                if osm
                else (
                    "Schematic coordinates and graph; no Taipei infrastructure or sighting "
                    "observations included."
                )
            ),
        },
        "assumptions": (
            OSM_ASSUMPTIONS
            + [
                "The origin cell is a suppressed aggregate of UNVERIFIED citizen reports; "
                "it is not an observed animal location.",
                "For a cell origin, walkers start uniformly from all eligible in-cell graph "
                "nodes; the cell does not identify one observed animal location.",
            ]
            if osm and resolved_cell
            else (OSM_ASSUMPTIONS if osm else SYNTHETIC_ASSUMPTIONS)
        ),
        "nodes": nodes,
        "edges": edges,
        "trajectories": trajectories,
        "trajectory_count": len(statistics.trajectories),
        "trajectory_truncated": len(statistics.trajectories) > len(trajectories),
    }
