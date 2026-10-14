"""Checks for transition probability contracts."""

from collections.abc import Iterable
from math import isclose


def probabilities_are_normalized(probabilities: Iterable[float]) -> bool:
    values = tuple(probabilities)
    return (
        bool(values)
        and all(value >= 0 for value in values)
        and isclose(sum(values), 1.0, abs_tol=1e-12)
    )
