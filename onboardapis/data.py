"""
This module contains everything that has to do with data and data management
"""
from __future__ import annotations

import logging
import threading
import time
from collections import UserDict

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from functools import wraps
from types import MethodType
from typing import Any, TypeVar, Generic, Callable, Tuple, Dict

from geopy.point import Point
from geopy.distance import geodesic
from restfly import APISession

from .units import coordinates_decimal_to_dms
from .exceptions import APIConnectionError
from . import __version__


def default(arg: Any | None, __default: Any | None = None, *, bool: bool = True) -> Any | None:  # noqa
    """
    Return ``data`` if there is actually some content in data, else return ``default``.

    Useful when data such as "" or b'' should also be treated as empty.

    :param Any arg: The data to test
    :param Any __default: The default value to return if no data is present (None)
    :param bool bool: Return the default if `arg` evaluates to False
    :return: The data if present, else the default
    :rtype: Optional[Any]
    """
    if bool:
        return arg if arg else __default
    return __default if arg is None else arg


T = TypeVar("T")
"""
A type variable for generic functions
"""


class ScheduledEvent(Generic[T]):
    """
    Something that is scheduled and can happen as ``scheduled``,
    but can also happen different from the expected and actually happens as ``actual``
    """

    __slots__ = ("scheduled", "actual")

    def __init__(self, scheduled: T, actual: T | None = None):
        """
        Initialize a new :class:`ScheduledEvent`

        :param scheduled: The value that should happen
        :type scheduled: T
        :param actual: The value that actually happens, will be the scheduled value if passed as None
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


@dataclass
class Position(object):
    """
    A position requires at least a latitude and longitude,
    but can also provide data on altitude and the current compass heading.
    """

    latitude: float
    """The latitude in decimal degrees"""
    longitude: float
    """The longitude in decimal degrees"""
    altitude: float = None
    """The altitude in meters"""
    heading: float = None
    """The compass heading in degrees"""

    def __str__(self) -> str:
        (lat_deg, lat_min, lat_sec), (lon_deg, lon_min, lon_sec,) = coordinates_decimal_to_dms(
            (self.latitude, self.longitude)
        )
        coordinates = (
            f"{abs(lat_deg)}°{lat_min}'{lat_sec:.3f}\"{'N' if lat_deg >= 0 else 'S'}"
            + f" {abs(lon_deg)}°{lon_min}'{lon_sec:.3f}\"{'E' if lon_deg >= 0 else 'W'}"
            + (f" {self.altitude:.2f}m" if self.altitude is not None else "")
            + (f" {self.heading:.2f}°" if self.heading is not None else "")
        )
        return coordinates

    def __getitem__(self, item):
        return ([self.latitude, self.longitude])[item]

    def calculate_distance(self, other: Position) -> float:
        """
        Calculate the distance (in meters) between this position and another position.

        :param other: The other position
        :return: The distance in meters
        """
        return geodesic(self.to_point(), other.to_point()).meters

    def to_point(self, altitude: bool = False) -> Point:
        return Point(self.latitude, self.longitude, altitude=self.altitude if altitude else None)


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

    def __init__(self) -> None:
        """
        Initialize a new :class:`DataConnector`
        """
        self._data = DataStorage()

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
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value


class PollingDataConnector(DataConnector, threading.Thread):
    _connected: bool
    _running: bool

    def __init__(self):
        DataConnector.__init__(self)
        threading.Thread.__init__(
            self,
            target=self._run,
            name=f"DataConnector-Runner for '{self.API_URL}'",
            daemon=True,
        )
        self._running = False
        self._connected = False

    @property
    def connected(self) -> bool:
        """
        Check whether the connector is connected to the server
        """
        return self._connected and self._running

    def _run(self) -> None:
        """
        The main loop that will run in a separate thread

        :return: Nothing
        :rtype: None
        """
        # thread join checks per second
        tps = 20
        counter = 0
        self._running = True
        while self._running:
            # If the counter is not 0, just wait and check for a thread join
            if counter != 0:
                time.sleep(1 / tps)
                counter = (counter + 1) % tps
                continue

            # The target time for when to perform the next refresh after this one
            target = time.time_ns() + int(1e9)

            try:
                self.refresh()
                self._connected = True
            except APIConnectionError as e:
                logging.getLogger(__name__).error(f"{e}")
                continue

            counter = (tps - int(max(0.0, (target - time.time_ns()) / 1e9) * tps)) % tps

    def stop(self) -> None:
        """
        Stop requesting data and shut down the separate thread
        """
        self._running = False
        if self.is_alive():
            self.join()

    def reset(self) -> None:
        """
        Reset the thread and the cache so that they can be reused with ``start()``
        """
        self.stop()
        threading.Thread.__init__(self)
        DataConnector.__init__(self)
        self._connected = False

    @abstractmethod
    def refresh(self) -> None:
        """
        Method that collects data from the server and stores it in the cache

        :return: Nothing
        """
        pass


class RESTDataConnector(APISession, PollingDataConnector, metaclass=ABCMeta):
    def __init__(self, **kwargs):
        kwargs['url'] = kwargs.pop('url', self.API_URL)
        APISession.__init__(self, **kwargs)
        PollingDataConnector.__init__(self)

    def _build_session(self, **kwargs) -> None:
        APISession._build_session(self, **kwargs)
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
    A dummy :class:`DataConnector` that does nothing and can be used for testing
    """

    API_URL = "127.0.0.1"

    def load(self, key: str, __default: Any = None) -> Any:
        return 'Dummy value'


T_return = TypeVar('T_return')


def store(name: str | MethodType = None) -> Callable[[MethodType], Callable[[DataConnector, tuple[Any, ...], dict[str, Any]], T_return]] | Callable[[DataConnector, tuple[Any, ...], dict[str, Any]], T_return]:
    """
    Decorator / decorator factory to apply to a :class:`DataConnector` method
    to immediately store the return value of the decorated method
    as the key ``name`` or the method name if left out.
    """
    def decorator(method: MethodType) -> Callable[[DataConnector, tuple[Any, ...], dict[str, Any]], T_return]:
        @wraps(method)
        def wrapper(self: DataConnector, *args, **kwargs) -> T_return:
            if isinstance(self, DataConnector):
                self[name or method.__name__] = method(self, *args, **kwargs)
                return self[name or method.__name__]
            return method(self, *args, **kwargs)

        return wrapper

    if isinstance(name, str) or name is None:
        return decorator

    if callable(name):
        m = name
        name = m.__name__
        return decorator(m)

    raise ValueError('You need to apply this decorator to a method of a DataConnector!')
    # Really any callable works just fine, but in this case the decorator will do nothing
