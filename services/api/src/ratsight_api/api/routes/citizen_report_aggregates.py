"""Suppressed 250 m aggregate of public citizen reports."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from ratsight_api.api.schemas import CitizenReportAggregateResponse
from ratsight_api.application.citizen_report_aggregates import (
    CitizenReportDataError,
    CitizenReportQueryError,
    CitizenReportStorageError,
    list_citizen_report_aggregates,
)
from ratsight_api.infrastructure.database.connection import get_session
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/citizen-report-aggregates", tags=["citizen-reports"])

STORAGE_UNAVAILABLE_DETAIL = "Citizen report storage unavailable"
INVALID_DATA_DETAIL = "Citizen report aggregate data is invalid"


class GeoJSONResponse(JSONResponse):
    media_type = "application/geo+json"


@router.get(
    "",
    response_model=CitizenReportAggregateResponse,
    response_class=GeoJSONResponse,
)
def get_citizen_report_aggregates(
    session: Annotated[Session, Depends(get_session)],
    bbox: str | None = None,
    months: str | None = None,
    report_type: str | None = None,
) -> Any:
    try:
        return list_citizen_report_aggregates(
            session,
            bbox=bbox,
            months=months,
            report_type=report_type,
        )
    except CitizenReportQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except CitizenReportStorageError as exc:
        raise HTTPException(status_code=503, detail=STORAGE_UNAVAILABLE_DETAIL) from exc
    except CitizenReportDataError as exc:
        raise HTTPException(status_code=500, detail=INVALID_DATA_DETAIL) from exc
