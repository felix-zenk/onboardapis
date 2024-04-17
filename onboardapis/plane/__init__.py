"""
Package for planes

## Operator ID

The operator ID for planes is the
[3 letter ICAO airline designator](https://en.wikipedia.org/wiki/List_of_airline_codes#Codes).
"""
from __future__ import annotations

from abc import ABCMeta

from .. import Vehicle

__all__ = [
    "Plane",
]


class Plane(Vehicle, metaclass=ABCMeta):
    """
    Base class for planes
    """
