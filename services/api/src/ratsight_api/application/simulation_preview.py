from ratsight_api.api.schemas import SimulationPreviewRequest
from ratsight_geo.osm import load_osm_surface_graph
from ratsight_simulation.graph.network import (
    SYNTHETIC_FIXTURE_ID,
    create_synthetic_graph,
    reachability_summary,
)
from ratsight_simulation.models.metadata import MODEL_ID, MODEL_VERSION
from ratsight_simulation.movement.random_walk import run_weighted_random_walk

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


def preview_simulation(request: SimulationPreviewRequest) -> dict[str, object]:
    osm = request.study_area == "taipei_osm_songshan"
    graph = load_osm_surface_graph() if osm else create_synthetic_graph()
    # Resolve by the string id the API exposes; never snap an unknown id to another node.
    node_by_id = {str(node_id): node_id for node_id in graph.nodes}
    requested_origin = request.origin_node_id
    if requested_origin is not None and requested_origin not in node_by_id:
        raise UnknownOriginNodeError(
            f"origin_node_id {requested_origin!r} is not a node in "
            f"study area {request.study_area!r}"
        )
    start_node = (
        node_by_id[requested_origin] if requested_origin is not None else next(iter(graph.nodes))
    )
    statistics = run_weighted_random_walk(
        graph,
        walkers=request.walkers,
        steps=request.duration_steps,
        seed=request.random_seed,
        start_node=start_node,
    )
    nodes = [
        {
            "id": str(node_id),
            "coordinates": graph.nodes[node_id]["coordinates"],
            "visits": statistics.node_visits[str(node_id)],
            "probability": statistics.node_probabilities[str(node_id)],
            "classification": "SIMULATED",
        }
        for node_id in graph.nodes
    ]
    edges = []
    for source, target, key, attributes in graph.edges(keys=True, data=True):
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
        for walker_id, trajectory in enumerate(statistics.trajectories[:100])
    ]
    return {
        "simulation_status": "completed",
        "classification": "SIMULATED",
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "origin": {
            "node_id": str(start_node),
            "coordinates": tuple(graph.nodes[start_node]["coordinates"]),
            "selection": "user" if requested_origin is not None else "default",
            "classification": "SIMULATED",
            "note": "Synthetic model input; not an observed or reported animal origin.",
        },
        "reachability": {
            **reachability_summary(graph, start_node),
            "classification": "SIMULATED",
            "note": (
                "Directed graph topology from the resolved origin; it is not habitat, "
                "food, sewer, or movement evidence."
            ),
        },
        "parameters": {
            "study_area": request.study_area,
            "origin_node_id": str(start_node),
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
        "assumptions": OSM_ASSUMPTIONS if osm else SYNTHETIC_ASSUMPTIONS,
        "nodes": nodes,
        "edges": edges,
        "trajectories": trajectories,
        "trajectory_count": len(statistics.trajectories),
        "trajectory_truncated": len(statistics.trajectories) > len(trajectories),
    }
