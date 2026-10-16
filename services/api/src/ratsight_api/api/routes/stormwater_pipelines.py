"""Stormwater infrastructure reference pipeline endpoint."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from ratsight_api.api.schemas import StormwaterResponse
from ratsight_api.application.stormwater_pipelines import (
    StormwaterDataError,
    StormwaterQueryError,
    StormwaterStorageError,
    list_stormwater_pipelines,
    parse_bbox,
)
from ratsight_api.infrastructure.database.connection import get_session
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/stormwater-pipelines", tags=["stormwater-pipelines"])

STORAGE_UNAVAILABLE_DETAIL = "Stormwater storage unavailable"
INVALID_DATA_DETAIL = "Stormwater data is invalid"


class GeoJSONResponse(JSONResponse):
    media_type = "application/geo+json"


@router.get(
    "",
    response_model=StormwaterResponse,
    response_class=GeoJSONResponse,
)
def get_stormwater_pipelines(
    session: Annotated[Session, Depends(get_session)],
    bbox: str | None = None,
) -> Any:
    try:
        parsed_bbox = parse_bbox(bbox)
    except StormwaterQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        return list_stormwater_pipelines(session, bbox=parsed_bbox)
    except StormwaterStorageError as exc:
        raise HTTPException(status_code=503, detail=STORAGE_UNAVAILABLE_DETAIL) from exc
    except StormwaterDataError as exc:
        raise HTTPException(status_code=500, detail=INVALID_DATA_DETAIL) from exc
