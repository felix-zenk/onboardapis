"""
This module contains everything that has to do with data and data management
"""
from __future__ import annotations

import logging
import threading
import time
from collections import UserDict

from abc import ABCMeta, abstractmethod
from typing import Any, Optional, TypeVar, Generic, Collection

from geopy.point import Point
from geopy.distance import geodesic
from restfly import APISession

from .conversions import coordinates_decimal_to_dms
from .exceptions import APIConnectionError, InitialConnectionError
from . import __version__


def default(
    arg: Optional[Any],
    __default: Optional[Any] = None,
    *,
    empty_collection: bool = False,
) -> Optional[Any]:
    """
    Return ``data`` if there is actually some content in data, else return ``default``.

    Useful when data such as "" or b'' should also be treated as empty.

    :param Any arg: The data to test
    :param Any __default: The default value to return if no data is present
    :param bool empty_collection: Treat an empty sequence as a missing value and return the default
    :return: The data if present, else the default
    :rtype: Optional[Any]
    """
    if arg is None:
        return __default
    if isinstance(arg, str) and arg == "":
        return __default
    if isinstance(arg, bytes) and arg == b"":
        return __default
    if empty_collection and isinstance(arg, Collection) and len(arg) == 0:
        return default
    return arg


T = TypeVar("T")
"""
A type variable for generic functions
"""


class ScheduledEvent(Generic[T]):
    """
    Something that is scheduled and can happen as ``scheduled``,
    but can also happen different from the expected and actually happens as ``actual``
    """

    __slots__ = ["scheduled", "actual"]

    def __init__(self, scheduled: T, actual: T | None = None):
        """
        Initialize a new :class:`ScheduledEvent`

        :param scheduled: The value that should happen
        :type scheduled: T
        :param actual: The value that actually happens
        :type actual: Optional[T]
        """
        self.scheduled = scheduled
        """
        The expected value of this event
        """
        self.actual = actual or scheduled
        """
        The actual value of this event, may differ from the scheduled value
        """

    def __repr__(self):
        if self.actual is None:
            return f"<{self.__class__.__name__} {self.scheduled}>"
        return f"<{self.__class__.__name__} {self.actual}>"

    def __str__(self):
        if self.actual is None:
            return f"{self.scheduled}"
        return f"{self.actual}"


class Position(object):
    """
    A position requires at least a latitude and longitude,
    but can also provide data on altitude and the current compass heading.
    """

    __slots__ = ["_latitude", "_longitude", "_altitude", "_bearing"]

    def __init__(
        self,
        latitude: float,
        longitude: float,
        altitude: float = None,
        bearing: float = None,
    ):
        """
        Initialize a new :class:`Position`.

        :param latitude: The latitude in decimal degrees
        :type latitude: float
        :param longitude: The longitude in decimal degrees
        :type longitude: float
        :param altitude: The altitude in meters
        :type altitude: float
        :param bearing: The compass heading in degrees
        :type bearing: float
        """
        self._latitude = latitude
        self._longitude = longitude
        self._altitude = altitude
        self._bearing = bearing

    def __str__(self) -> str:
        (lat_deg, lat_min, lat_sec), (
            lon_deg,
            lon_min,
            lon_sec,
        ) = coordinates_decimal_to_dms((self.latitude, self.longitude))
        coordinates = (
            f"{abs(lat_deg)}°{lat_min}'{lat_sec:.3f}\"{'N' if lat_deg >= 0 else 'S'}"
            + f" {abs(lon_deg)}°{lon_min}'{lon_sec:.3f}\"{'E' if lon_deg >= 0 else 'W'}"
            + (f" {self.altitude:.2f}m" if self.altitude is not None else "")
            + (f" {self.bearing:.2f}°" if self.bearing is not None else "")
        )
        return coordinates

    def __getitem__(self, item):
        return list([self.latitude, self.longitude])[item]

    @property
    def latitude(self) -> float:
        """
        The latitude in decimal degrees.

        :return: The latitude
        :rtype: float
        """
        return float(self._latitude)

    @property
    def longitude(self) -> float:
        """
        The longitude in decimal degrees.

        :return: The longitude
        :rtype: float
        """
        return float(self._longitude)

    @property
    def altitude(self) -> float:
        """
        The altitude in meters.

        :return: The altitude
        :rtype: float
        """
        return float(self._altitude)

    @property
    def bearing(self) -> float:
        """
        The compass heading in degrees.

        0 is north, 90 is east, 180 is south, 270 is west.

        :return: The heading
        :rtype: float
        """
        return float(self._bearing)

    def calculate_distance(self, other: Position) -> float:
        """
        Calculate the distance (in meters) between this position and another position.

        :param other: The other position
        :return: The distance in meters
        """
        return geodesic(
            Point(
                latitude=self.latitude, longitude=self.longitude
            ),  # altitude not supported
            Point(
                latitude=other.latitude, longitude=other.longitude
            ),  # altitude not supported
        ).meters


class DataStorage(UserDict):
    """
    A storage class that can be used to store data and retrieve it later.
    """


class DataConnector(metaclass=ABCMeta):
    """
    A class for retrieving data from an API
    """

    API_URL: str
    """
    The base URL under which the API can be accessed
    """

    _data: DataStorage
    _runner: threading.Thread
    _initialized: bool
    _running: bool

    def __init__(self) -> None:
        """
        Initialize a new :class:`DataConnector`
        """
        self._data = DataStorage()
        self._runner = threading.Thread(
            target=self._run,
            name=f"DataConnector-Runner for '{self.API_URL}'",
            daemon=True,
        )
        self._running = False
        self._initialized = False

    def load(self, key: str, __default: Any = None) -> Any:
        """
        Load data from the cache

        :param key: The key to load
        :param __default: The default value to return if the key is not present
        :return: The data if present, else the default
        """
        return self._data.get(key, __default)

    def store(self, key: str, value: Any) -> None:
        """
        Store data in the cache

        :param key: The key the data should be stored under
        :param value: The data to store
        :return: Nothing
        """
        self._data[key] = value

    def __getitem__(self, item):
        return self.load(item)

    def __setitem__(self, key, value):
        self.store(key, value)

    @property
    def connected(self) -> bool:
        """
        Check whether the connector is connected to the server
        """
        return self._initialized and self._running

    def _run(self) -> None:  # TODO overhaul
        """
        The main loop that will run in a separate thread

        :return: Nothing
        :rtype: None
        """
        # tps is the amount of checks per second for a thread join while waiting for the next refresh
        # During a refresh it does not check for a thread join
        tps = 20  # 20 ticks per second -> check for thread join every 0.05 seconds, refresh the data each second

        counter = 0
        while self._running:
            # If the counter is not 0, just wait and check for a thread join (self._running == False)
            if counter != 0:
                time.sleep(1 / tps)
                counter = (counter + 1) % tps
                continue

            # The target time for when to perform the next refresh after this one
            target = time.time_ns() + int(1e9)

            # Perform the actual refresh
            try:
                self.refresh()
            except APIConnectionError as e:
                self._running = False
                logging.getLogger(__name__).error(f"{e}")
                continue

            # Signal that the data has been refreshed at least once (for thread synchronization)
            if not self._initialized:
                self._initialized = True

            # Calculate the tps to wait until the next refresh
            counter = (tps - int(max(0.0, (target - time.time_ns()) / 1e9) * tps)) % tps

    def start(self) -> None:
        """
        Start requesting data
        """
        self._running = True
        self._runner.start()
        while self._runner.is_alive() and not self._initialized:  # pragma: no cover
            # Wait until the new thread has initialized (received data at least once)
            pass

        if not self._runner.is_alive():
            # If the thread is not alive, something went wrong
            self.reset()
            raise InitialConnectionError("Failed to connect to the server")

    def stop(self) -> None:
        """
        Stop requesting data and shut down the separate thread
        """
        self._running = False
        if self._runner.is_alive():
            self._runner.join()

    def reset(self) -> None:
        """
        Reset the thread and the cache so that they can be reused with ``start()``
        """
        self.stop()
        self.__init__()

    @abstractmethod
    def refresh(self) -> None:
        """
        Method that collects data from the server and stores it in the cache

        :return: Nothing
        """
        pass


class RESTDataConnector(APISession, DataConnector, metaclass=ABCMeta):
    def __init__(self, **kwargs):
        kwargs['_url'] = kwargs.pop('_url', self.API_URL)
        super().__init__(**kwargs)

    def _build_session(self, **kwargs) -> None:
        super()._build_session(**kwargs)
        self._session.headers.update(
            {"user-agent": f"python-onboardapis/{__version__}"}
        )


class GraphQLDataConnector(DataConnector, metaclass=ABCMeta):
    pass


class WebsocketDataConnector(DataConnector, metaclass=ABCMeta):
    pass


class SocketIODataConnector(DataConnector, metaclass=ABCMeta):
    pass


class DummyDataConnector(DataConnector):
    """
    A dummy :class:`DataConnector` that can be used if the API does not supply static or dynamic data
    """

    API_URL = "127.0.0.1"

    def refresh(self) -> None:
        pass

    def start(self) -> None:
        self._initialized = True
        self._running = True

    def stop(self) -> None:
        self._running = False

    def reset(self) -> None:
        self.stop()
        self._initialized = False
