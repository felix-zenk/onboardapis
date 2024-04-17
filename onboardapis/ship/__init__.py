"""
Package for ships

## Operator ID

The operator ID for ships is the <undefined>.
"""
from __future__ import annotations

from abc import ABCMeta

from .. import Vehicle

__all__ = [
    "Ship",
]


class Ship(Vehicle, metaclass=ABCMeta):
    """
    Base class for ships
    """
