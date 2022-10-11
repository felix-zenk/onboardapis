"""
Package metadata
"""

__project_name__ = 'onboardapis'
__description__ = 'A pure Python wrapper for the on-board APIs of many different transportation providers'
__version__ = '1.2.3'
__author__ = 'Felix Zenk'
__email__ = 'felix.zenk@web.de'
__license__ = 'MIT'
__copyright__ = 'Copyright (c) 2022 Felix Zenk'
__url__ = 'https://github.com/felix-zenk/onboardapis'

from abc import ABCMeta


class Vehicle(object):
    """
    The base class for all vehicles.
    """

    __slots__ = []


class IncompleteVehicleMixin(object, metaclass=ABCMeta):
    """
    Base class for mixins that implement the abstract methods of their bases
    if the API does not provide the requested data.
    """
    pass
