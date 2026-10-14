"""Only a no-intervention baseline exists in this initialization."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    scenario_id: str = "baseline"
    implemented: bool = False
    description: str = "No intervention effect is modeled."
