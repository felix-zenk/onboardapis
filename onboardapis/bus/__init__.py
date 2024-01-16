"""
Package for buses

## Operator ID

The operator ID for buses is highly dependent on the region
and will be described further in the according country package.
"""
from __future__ import annotations
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

from abc import ABCMeta

from .. import Vehicle

__all__ = [
    'Bus',
]


class Bus(Vehicle, metaclass=ABCMeta):
    """
    Base class for buses
    """
