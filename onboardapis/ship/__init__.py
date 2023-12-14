"""
Package for ships
"""
from __future__ import annotations
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

from abc import ABCMeta

from .. import Vehicle


class Ship(Vehicle, metaclass=ABCMeta):
    pass
