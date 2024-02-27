"""
Module for data generation and processing.

This module contains classes and functions that are used to generate and process data fetched from the APIs.
It also provides common data structures that are used throughout the library.
"""
from __future__ import annotations

import importlib.metadata
import logging
import threading
import time

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import TypeVar, Generic, ClassVar

from geopy.point import Point
from geopy.distance import geodesic
from restfly import APISession

from .units import coordinates_decimal_to_dms
from .exceptions import APIConnectionError


def default(arg, __default=None, *, bool=True):  # noqa
    """
    Return ``data`` if there is actually some content in data, else return ``default``.

    Useful when data such as "" or b'' should also be treated as empty.

    :param arg: The data to test
    :param __default: The default value to return if no data is present (None)
    :param bool: Return the default if `arg` evaluates to False
    :return: The data if present, else the default
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

    def __init__(self, scheduled, actual=None):
        """
        Initialize a new :class:`ScheduledEvent`

        :param scheduled: The value that should happen
        :param actual: The value that actually happens, will be the scheduled value if passed as None
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
    altitude = None
    """The altitude in meters"""
    heading = None
    """The compass heading in degrees"""

    def __str__(self):
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

    def calculate_distance(self, other):
        """
        Calculate the distance (in meters) between this position and another position.

        :param other: The other position
        :return: The distance in meters
        """
        return geodesic(self.to_point(), other.to_point()).meters

    def to_point(self, altitude=False):
        return Point(self.latitude, self.longitude, altitude=self.altitude if altitude else None)


class DataConnector(metaclass=ABCMeta):
    """
    A class for retrieving data from an API
    """
    API_URL: ClassVar[str]
    """The base URL for the API."""

    def __init__(self):
        """Initialize a new :class:`DataConnector`."""
        self._data = dict()

    def load(self, key, __default=None):
        """
        Load data from the cache

        :param key: The key to load
        :param __default: The default value to return if the key is not present
        :return: The data if present, else the default
        """
        return self._data.get(key, __default)

    def store(self, key, value):
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


class ThreadedDataConnector(DataConnector, threading.Thread):
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
    def connected(self):
        """
        Check whether the connector is connected to the server
        """
        return self._connected and self._running

    def _run(self):
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

    def stop(self):
        """
        Stop requesting data and shut down the separate thread
        """
        self._running = False
        if self.is_alive():
            self.join()

    def reset(self):
        """
        Reset the thread and the cache so that they can be reused with ``start()``
        """
        self.stop()
        threading.Thread.__init__(self)
        DataConnector.__init__(self)
        self._connected = False

    @abstractmethod
    def refresh(self):
        """
        Method that collects data from the server and stores it in the cache

        :return: Nothing
        """
        raise NotImplementedError


class BlockingRESTDataConnector(APISession, DataConnector):
    """A RESTful :class:`DataConnector` that uses the :class:`APISession` to fetch."""

    def __init__(self, **kwargs):
        kwargs['url'] = kwargs.pop('url', self.API_URL)
        APISession.__init__(self, **kwargs)
        DataConnector.__init__(self)

    def _build_session(self, **kwargs):
        def _get_package_version():
            """Return the version of the onboardapis package."""
            try:
                return importlib.metadata.version('onboardapis')
            except importlib.metadata.PackageNotFoundError:
                return 'unknown'

        APISession._build_session(self, **kwargs)
        self._session.headers.update({"User-Agent": f"Python/onboardapis ({_get_package_version()})"})


class ThreadedRESTDataConnector(ThreadedDataConnector, BlockingRESTDataConnector, metaclass=ABCMeta):
    """A RESTful :class:`DataConnector` that uses the :class:`APISession` to fetch data."""

    def __init__(self, **kwargs):
        kwargs['url'] = kwargs.pop('url', self.API_URL)
        APISession.__init__(self, **kwargs)
        ThreadedDataConnector.__init__(self)


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

    def load(self, key, __default=None):
        return 'Dummy value'


def store(name=None):
    """
    Decorator / decorator factory to apply to a :class:`DataConnector` method
    to immediately store the return value of the decorated method
    as the key ``name`` or the method name if left out.
    """
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
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


class InternetAccessInterface(metaclass=ABCMeta):
    """
    Interface adding functions for connecting and disconnecting to the internet
    as well as viewing the current status.
    """
    _is_enabled = False
    """Cached information on connection status"""

    @abstractmethod
    def enable(self):
        """Enable the internet access for this device.

        Request internet access for this device by automatically accepting the terms of service
        and signing in to the captive portal.

        Raises:
            ConnectionError: If the internet access is temporarily not available.
        """
        self._is_enabled = True

    @abstractmethod
    def disable(self):
        """Disable the internet access for this device.

        Disable the internet access for this device by signing out of the captive portal.

        Raises:
            ConnectionError: If the internet access is temporarily not available.
        """
        if not self.is_enabled:
            return

        self._is_enabled = False

    @property
    def is_enabled(self):
        """Return whether the internet access is enabled for this device."""
        return self._is_enabled


class InternetMetricsInterface(metaclass=ABCMeta):
    """
    Interface for information on limited internet access.
    """
    @abstractmethod
    def limit(self):
        """Return the total internet access quota in MB or `None` if there is none."""
