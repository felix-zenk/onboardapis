"""
Package for planes
"""
from abc import ABCMeta

from .. import Vehicle
from ..mixins import PositionMixin


class Plane(Vehicle, PositionMixin, metaclass=ABCMeta):
    pass
