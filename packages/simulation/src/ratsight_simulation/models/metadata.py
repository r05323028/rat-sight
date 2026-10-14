"""Versioned model identity; model runs remain explicitly simulated."""

from dataclasses import dataclass

MODEL_ID = "synthetic_weighted_random_walk"
MODEL_VERSION = "0.1.0"


@dataclass(frozen=True)
class ModelMetadata:
    model_id: str = MODEL_ID
    model_version: str = MODEL_VERSION
    classification: str = "SIMULATED"
    status: str = "demonstration"
