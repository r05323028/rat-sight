"""Composable edge constraints; no biological constraint is assumed by default."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class EdgeConstraint(Protocol):
    """A domain-reviewed constraint that may exclude a candidate transition."""

    def allows(self, source: str, target: str, edge: Mapping[str, Any], step: int) -> bool: ...
