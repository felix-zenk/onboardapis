"""
Package for ships
"""
from abc import ABCMeta

from .. import Vehicle


class Ship(Vehicle, metaclass=ABCMeta):
    pass
