from fastapi import APIRouter
from ratsight_api.api.schemas import SystemStatusResponse
from ratsight_api.application.system_status import system_status

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status() -> dict[str, object]:
    return system_status()
