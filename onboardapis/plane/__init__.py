"""
Package for planes

## Operator ID

The operator ID for planes is the
[3-letter ICAO airline designator](https://en.wikipedia.org/wiki/List_of_airline_codes#Codes).

---
"""
from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass

from .. import Vehicle, Station
from ..data import ScheduledEvent

__all__ = [
    "Plane",
    "Airport",
    "cz",
    "de",
    "ee",
    "no",
    "third_party",
]


class Plane(Vehicle, metaclass=ABCMeta):
    """
    Base class for planes
    """


@dataclass
class Airport(Station):
    """An `onboardapis.Station` with the additional information of a gate."""
    gate: ScheduledEvent[str] | None
    """The gate where the plane is parked at."""
