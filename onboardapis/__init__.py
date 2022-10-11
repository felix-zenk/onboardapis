"""
Package metadata and base classes.
"""

__project_name__ = 'onboardapis'
__description__ = 'A pure Python wrapper for the on-board APIs of many different transportation providers'
__version__ = '1.3.1'
__author__ = 'Felix Zenk'
__email__ = 'felix.zenk@web.de'
__license__ = 'MIT'
__copyright__ = 'Copyright (c) 2022 Felix Zenk'
__url__ = 'https://github.com/felix-zenk/onboardapis'

from abc import ABCMeta

from .exceptions import APIConnectionError, InitialConnectionError
from .utils.data import StaticDataConnector, DynamicDataConnector, DummyDataConnector


class Vehicle(object):
    """
    The base class for all vehicles.
    """
    __slots__ = ["_static_data", "_dynamic_data", "_initialized"]

    def __init__(self):
        self._initialized = False
        self._static_data: StaticDataConnector = DummyDataConnector()
        self._dynamic_data: DynamicDataConnector = DummyDataConnector()

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def init(self) -> None:
        """
        Initialize the :class:`DataConnector` objects.

        Calls ``refresh`` on the :class:`StaticDataConnector`
        and ``start`` on the :class:`DynamicDataConnector` by default.

        :return: Nothing
        :rtype: None
        """
        if self._initialized:
            return
        try:
            self._dynamic_data.start()
            self._static_data.refresh()
            self._initialized = True
        except APIConnectionError as e:
            raise InitialConnectionError() from e

    def shutdown(self) -> None:
        """
        Safely close the :class:`DataConnector` objects of this vehicle.

        :return: Nothing
        :rtype: None
        """
        self._dynamic_data.stop()

    @property
    def connected(self) -> bool:
        """
        Whether the vehicle is connected to the API

        :return: Whether the vehicle is connected to the API
        :rtype: bool
        """
        return self._dynamic_data.connected


class IncompleteVehicleMixin(object, metaclass=ABCMeta):
    """
    Base class for mixins that implement the abstract methods of their bases
    if the API does not provide the requested data.
    """
    pass
