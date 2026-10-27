from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from ratsight_api.api.schemas import (
    ModelCatalogItem,
    SimulationPreviewRequest,
    SimulationPreviewResponse,
)
from ratsight_api.application.simulation_preview import (
    OriginCellResolutionError,
    OriginCellStorageError,
    OriginReportTypeIneligibleError,
    OriginSourceUnknownError,
    OriginSourceVersionConflictError,
    UnknownOriginNodeError,
    preview_simulation,
)
from ratsight_api.domain.citizen_report_aggregates import ORIGIN_POLICY_VERSION
from ratsight_api.infrastructure.database.connection import get_session
from ratsight_simulation.models.metadata import MODEL_ID, MODEL_VERSION
from sqlalchemy.orm import Session

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
def create_preview(
    request: SimulationPreviewRequest,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, object]:
    try:
        return preview_simulation(request, session=session)
    except OriginSourceVersionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ORIGIN_SOURCE_VERSION_CONFLICT",
                "message": "The selected citizen-report dataset is no longer current.",
                "action": "Refresh citizen reports and select an origin again.",
                "dataset_id": (request.origin_source.dataset_id if request.origin_source else None),
                "resource_version": (
                    request.origin_source.resource_version if request.origin_source else None
                ),
            },
        ) from exc
    except OriginSourceUnknownError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ORIGIN_SOURCE_UNKNOWN",
                "message": str(exc),
                "action": "Select a published citizen-report dataset and try again.",
                "dataset_id": (request.origin_source.dataset_id if request.origin_source else None),
            },
        ) from exc
    except OriginReportTypeIneligibleError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ORIGIN_REPORT_TYPE_INELIGIBLE",
                "message": str(exc),
                "reason": exc.reason,
                "report_type": exc.report_type,
                "origin_cell_id": request.origin_cell_id,
                "policy_version": ORIGIN_POLICY_VERSION,
                "classification": "UNVERIFIED",
            },
        ) from exc
    except OriginCellResolutionError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ORIGIN_CELL_NOT_RESOLVABLE",
                "message": str(exc),
                "origin_cell_id": request.origin_cell_id,
                "classification": "UNVERIFIED",
            },
        ) from exc
    except OriginCellStorageError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ORIGIN_CELL_STORAGE_UNAVAILABLE",
                "message": str(exc),
                "origin_cell_id": request.origin_cell_id,
            },
        ) from exc
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
                    "~/.local/share/ratsight/network/taipei-expanded-ratdar-20261027.osm; "
                    "see docs/infrastructure/taipei-osm-network-source.md."
                ),
            },
        ) from exc
