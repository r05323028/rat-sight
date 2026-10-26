from fastapi import APIRouter, HTTPException
from ratsight_api.api.schemas import (
    ModelCatalogItem,
    SimulationPreviewRequest,
    SimulationPreviewResponse,
)
from ratsight_api.application.simulation_preview import UnknownOriginNodeError, preview_simulation
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
    try:
        return preview_simulation(request)
    except UnknownOriginNodeError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ORIGIN_NODE_NOT_IN_GRAPH",
                "message": str(exc),
                "study_area": request.study_area,
            },
        ) from exc
    except (FileNotFoundError, ValueError) as exc:
        if request.study_area != "taipei_osm_songshan":
            raise
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SOURCE_NETWORK_UNAVAILABLE",
                "message": str(exc),
                "provisioning": (
                    "Place the pinned extract at "
                    "~/.local/share/ratsight/network/taipei-songshan-20261023.osm; "
                    "see docs/infrastructure/taipei-osm-network-source.md."
                ),
            },
        ) from exc
