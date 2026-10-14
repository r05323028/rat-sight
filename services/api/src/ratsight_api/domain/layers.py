from dataclasses import dataclass

from ratsight_api.domain.classification import EvidenceClass


@dataclass(frozen=True)
class LayerDefinition:
    layer_id: str
    label: str
    classification: EvidenceClass | None
    message: str


LAYER_CATALOG = (
    LayerDefinition(
        "rodent_observations", "Rodent observations", None, "No observation dataset loaded."
    ),
    LayerDefinition("sewer_networks", "Sewer networks", None, "No sewer dataset loaded."),
    LayerDefinition(
        "stormwater_networks", "Stormwater networks", None, "No stormwater dataset loaded."
    ),
    LayerDefinition(
        "surface_corridors", "Surface movement corridors", None, "No corridor dataset loaded."
    ),
    LayerDefinition("human_activity", "Human activity", None, "No human-activity dataset loaded."),
    LayerDefinition(
        "environmental_conditions",
        "Environmental conditions",
        None,
        "No environmental dataset loaded.",
    ),
    LayerDefinition(
        "simulated_paths",
        "Simulated movement paths",
        "SIMULATED",
        "Available after a synthetic preview.",
    ),
)
