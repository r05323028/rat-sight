"""Administrative reference district boundary endpoint."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from ratsight_api.api.schemas import AdministrativeDistrictResponse
from ratsight_api.application.administrative_districts import (
    AdministrativeDistrictDataError,
    AdministrativeDistrictStorageError,
    list_administrative_districts,
)
from ratsight_api.infrastructure.database.connection import get_session
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/administrative-districts", tags=["administrative-districts"])

STORAGE_UNAVAILABLE_DETAIL = "Administrative district storage unavailable"
INVALID_DATA_DETAIL = "Administrative district data is invalid"


class GeoJSONResponse(JSONResponse):
    media_type = "application/geo+json"


@router.get(
    "",
    response_model=AdministrativeDistrictResponse,
    response_class=GeoJSONResponse,
)
def get_administrative_districts(
    session: Annotated[Session, Depends(get_session)],
) -> Any:
    try:
        return list_administrative_districts(session)
    except AdministrativeDistrictStorageError as exc:
        raise HTTPException(status_code=503, detail=STORAGE_UNAVAILABLE_DETAIL) from exc
    except AdministrativeDistrictDataError as exc:
        raise HTTPException(status_code=500, detail=INVALID_DATA_DETAIL) from exc
