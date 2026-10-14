"""Explicit unknown parameters remain unknown until evidence supports values."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterCalibration:
    parameter_id: str
    value: float | None = None
    unit: str | None = None
    source_evidence_ids: tuple[str, ...] = ()
    calibration_status: str = "not_calibrated"
    validation_status: str = "not_validated"
