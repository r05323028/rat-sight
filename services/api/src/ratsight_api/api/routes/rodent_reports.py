"""Fixture-only rodent report endpoint."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from ratsight_api.api.schemas import RodentReportResponse
from ratsight_api.application.rodent_reports import (
    RodentReportDataError,
    RodentReportQueryError,
    RodentReportStorageError,
    list_rodent_reports,
)
from ratsight_api.infrastructure.database.connection import get_session
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/rodent-reports", tags=["rodent-reports"])

STORAGE_UNAVAILABLE_DETAIL = "Rodent report storage unavailable"
INVALID_DATA_DETAIL = "Rodent report data is invalid"


class GeoJSONResponse(JSONResponse):
    media_type = "application/geo+json"


@router.get(
    "",
    response_model=RodentReportResponse,
    response_class=GeoJSONResponse,
)
def get_rodent_reports(
    session: Annotated[Session, Depends(get_session)],
    bbox: str | None = None,
    reported_from: str | None = None,
    reported_to: str | None = None,
) -> Any:
    try:
        return list_rodent_reports(
            session,
            bbox=bbox,
            reported_from=reported_from,
            reported_to=reported_to,
        )
    except RodentReportQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RodentReportStorageError as exc:
        raise HTTPException(status_code=503, detail=STORAGE_UNAVAILABLE_DETAIL) from exc
    except RodentReportDataError as exc:
        raise HTTPException(status_code=500, detail=INVALID_DATA_DETAIL) from exc
