"""
Package for buses
"""
from abc import ABCMeta

from .. import Vehicle


class Bus(Vehicle, metaclass=ABCMeta):
    pass
