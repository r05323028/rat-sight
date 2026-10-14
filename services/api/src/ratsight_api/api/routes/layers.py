from fastapi import APIRouter
from ratsight_api.api.schemas import LayerResponse
from ratsight_api.application.layers import list_layers

router = APIRouter(prefix="/api/v1/layers", tags=["layers"])


@router.get("", response_model=list[LayerResponse])
def get_layers() -> list[dict[str, object]]:
    return list_layers()
