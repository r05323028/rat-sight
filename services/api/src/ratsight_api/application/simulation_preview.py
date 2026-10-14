from ratsight_api.api.schemas import SimulationPreviewRequest
from ratsight_simulation.graph.network import (
    SYNTHETIC_FIXTURE_ID,
    create_synthetic_graph,
)
from ratsight_simulation.models.metadata import MODEL_ID, MODEL_VERSION
from ratsight_simulation.movement.random_walk import run_weighted_random_walk

ASSUMPTIONS = [
    (
        "Graph topology, coordinates, and movement weights are synthetic fixtures, "
        "not surveyed infrastructure or animal observations."
    ),
    (
        "Transition probability is proportional to positive outgoing movement_weight; "
        "weights are unitless placeholders and are not calibrated biological parameters."
    ),
    (
        "No intervention, population dynamics, environmental effect, "
        "or real-world risk is represented."
    ),
]


def preview_simulation(request: SimulationPreviewRequest) -> dict[str, object]:
    graph = create_synthetic_graph()
    statistics = run_weighted_random_walk(
        graph,
        walkers=request.walkers,
        steps=request.duration_steps,
        seed=request.random_seed,
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
    edges = [
        {
            "source": source,
            "target": target,
            "edge_id": str(attributes["edge_id"]),
            "movement_weight": float(attributes["movement_weight"]),
            "visits": statistics.edge_visits[
                (str(source), str(target), str(attributes["edge_id"]))
            ],
            "probability": statistics.edge_probabilities[
                (str(source), str(target), str(attributes["edge_id"]))
            ],
            "classification": "SIMULATED",
        }
        for source, target, _, attributes in graph.edges(keys=True, data=True)
    ]
    return {
        "simulation_status": "completed",
        "classification": "SIMULATED",
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "parameters": {
            "study_area": request.study_area,
            "duration_steps": request.duration_steps,
            "walkers": request.walkers,
            "random_seed": request.random_seed,
            "movement_model": request.movement_model,
            "intervention_scenario": request.intervention_scenario,
        },
        "provenance": {
            "classification": "SIMULATED",
            "source_type": "synthetic_fixture",
            "source_id": SYNTHETIC_FIXTURE_ID,
            "source_crs": "EPSG:4326",
            "note": (
                "Schematic coordinates and graph; no Taipei infrastructure or sighting "
                "observations included."
            ),
        },
        "assumptions": ASSUMPTIONS,
        "nodes": nodes,
        "edges": edges,
    }
