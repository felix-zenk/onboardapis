"""
Package for planes
"""
from __future__ import annotations
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

from abc import ABCMeta

from .. import Vehicle
from ..mixins import PositionMixin


class Plane(Vehicle, PositionMixin, metaclass=ABCMeta):
    pass
