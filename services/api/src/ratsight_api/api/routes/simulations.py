from fastapi import APIRouter
from ratsight_api.api.schemas import (
    ModelCatalogItem,
    SimulationPreviewRequest,
    SimulationPreviewResponse,
)
from ratsight_api.application.simulation_preview import preview_simulation
from ratsight_simulation.models.metadata import MODEL_ID, MODEL_VERSION

router = APIRouter(prefix="/api/v1/simulations", tags=["simulations"])


@router.get("/models", response_model=list[ModelCatalogItem])
def get_models() -> list[ModelCatalogItem]:
    return [
        ModelCatalogItem(
            id=MODEL_ID,
            version=MODEL_VERSION,
            status="demonstration",
            classification="SIMULATED",
            description=(
                "Seeded weighted random walk on a schematic synthetic graph; "
                "not a real-world prediction."
            ),
        )
    ]


@router.post("/preview", response_model=SimulationPreviewResponse)
def create_preview(request: SimulationPreviewRequest) -> dict[str, object]:
    return preview_simulation(request)
