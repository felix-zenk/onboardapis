"""
Module for data generation and processing.

This module contains classes and functions that are used to generate and process data fetched from the APIs.
It also provides common data structures that are used throughout the library.
"""
from __future__ import annotations

import importlib.metadata
import logging
import time

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from functools import wraps
from json import JSONDecodeError
from typing import TypeVar, Generic, ClassVar, Any
from threading import Thread

from geopy.point import Point
from geopy.distance import geodesic
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from restfly import APISession

from .units import coordinates_decimal_to_dms
from .exceptions import APIConnectionError, InitialConnectionError

__all__ = [
    "ID",
    "StationType",
    "get_package_version",
    "default",
    "ScheduledEvent",
    "Position",
    "API",
    "store",
    "ThreadedAPI",
    "BlockingRestAPI",
    "ThreadedRestAPI",
    "BlockingGraphQlAPI",
    "ThreadedGraphQlAPI",
]

logger = logging.getLogger(__name__)

T = TypeVar("T")
"""A type variable for generics."""

ID = TypeVar("ID", str, int)
"""A TypeVar indicating the return type of Vehicle.id"""

StationType = TypeVar("StationType", bound="Station")
"""A TypeVar indicating the Station type"""

ApiType = TypeVar("ApiType", bound="API")
"""A TypeVar indicating the API type"""


def get_package_version() -> str:
    """Return the version of the ``onboardapis`` package."""
    try:
        return importlib.metadata.version('onboardapis')
    except importlib.metadata.PackageNotFoundError:
        return 'unknown'


def default(arg: Any, default: Any = None, *, boolean: bool = True) -> Any:  # noqa: F402
    """Return ``arg`` if it evaluates to ``True``, else return ``default``.

    Set ``boolean`` to ``False`` to only test for ``arg=None``.

    Args:
        arg: The data to test.
        default: The default value to return if no data is present.
        boolean: Return the default if `arg` evaluates to False.

    Returns:
        The data if present, else the default.
    """
    if boolean:
        return arg if arg else default
    return default if arg is None else arg


class ScheduledEvent(Generic[T]):
    """
    An event that is scheduled to have the value ``scheduled``,
    but can also happen different from the expected and actually happens as ``actual``.
    """

    scheduled: T
    """The expected value of this event."""
    actual: T
    """The actual value of this event."""

    def __init__(self, scheduled: T, actual: T | None = None) -> None:
        """
        Initialize a new :class:`ScheduledEvent`.

        Args:
            scheduled: The value that should happen.
            actual: The value that actually happens, will be the same as the scheduled value if passed as None.
        """
        self.scheduled = scheduled
        self.actual = actual or scheduled

    def __str__(self):
        return str(self.scheduled) if self.actual is None else str(self.actual)


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
        return (self.latitude, self.longitude)[item]

    def calculate_distance(self, other: Position | Point) -> float:
        """
        Calculate the distance (in meters) between this position and another position.

        :param other: The other position
        :return: The distance in meters
        """
        if not isinstance(other, (Position, Point)):
            raise ValueError
        return geodesic(self.to_point(), other.to_point() if isinstance(other, Position) else other).meters

    def to_point(self, with_altitude: bool = False) -> Point:
        """Convert to a ``geopy.point.Point``."""
        return Point(self.latitude, self.longitude, altitude=self.altitude if with_altitude else None)


class API(metaclass=ABCMeta):
    """A class for retrieving data from an API."""

    API_URL: ClassVar[str]
    """The base URL for the API."""

    def __init__(self):
        """Initialize a new ``API``."""
        self._data = dict()

    def load(self, key: str, default: Any = None) -> Any:  # noqa: F402
        """Load data from the cache.

        Args:
            key: The key to load.
            default: The default value to return if the key is not present.

        Returns:
            The data if present, else the default.
        """
        return self._data.get(key, default)

    def store(self, key: str, value: Any) -> None:
        """Store data in the cache.

        Args:
            key: The key the data should be stored under.
            value: The data to store.
        """
        self._data[key] = value

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value


def store(name=None):
    """
    Decorator / decorator factory to apply to an ``API`` method
    to immediately store the return value of the decorated method
    as the key ``name`` or the method name if left out.
    """
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if isinstance(self, API):
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

    raise ValueError('You need to apply this decorator to a method of an API!')
    # Really any callable works just fine, but in this case the decorator will do nothing


class ThreadedAPI(API, Thread):
    """An ``API`` that refreshes the data in a new thread."""

    _is_running: bool
    _is_connected: bool

    def __init__(self) -> None:
        """Initialize a new ``ThreadedAPI``."""
        API.__init__(self)
        Thread.__init__(
            self,
            target=self._run,
            name=f"API-Thread for '{self.API_URL}'",
            daemon=True,
        )
        self._is_running = False
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check whether the connector is connected to the server"""
        return self._is_connected and self._is_running

    def _run(self) -> None:
        """The main loop that will run in a separate thread."""
        # thread join checks per second
        tps = 20
        counter = 0
        self._is_running = True
        while self._is_running:
            # If the counter is not 0, just wait and check for a thread join
            if counter != 0:
                time.sleep(1 / tps)
                counter = (counter + 1) % tps
                continue

            # The target time for when to perform the next refresh after this one
            target = time.time_ns() + int(1e9)

            try:
                self.refresh()
                self._is_connected = True
            except (APIConnectionError, JSONDecodeError) as e:
                if not self._is_connected:
                    raise InitialConnectionError from e
                logger.error(f"{e}")
                continue

            counter = (tps - int(max(0.0, (target - time.time_ns()) / 1e9) * tps)) % tps

    def stop(self) -> None:
        """Stop requesting data and shut down the separate thread."""
        self._is_running = False
        if self.is_alive():
            self.join()

    def reset(self) -> None:
        """Reset the thread and the cache so that they can be reused with ``start()``."""
        self.stop()
        Thread.__init__(self)
        API.__init__(self)
        self._is_connected = False

    @abstractmethod
    def refresh(self) -> None:
        """Method that collects data from the server and stores it in the cache."""
        raise NotImplementedError


class BlockingRestAPI(APISession, API):
    """A RESTful ``API`` that uses an ``restfly.session.APISession`` to fetch data."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a new ``BlockingRestAPI``.

        Args:
            kwargs: The kwargs to pass to the underlying ``restfly.session.APISession``.
        """
        kwargs['url'] = kwargs.pop('url', self.API_URL)
        APISession.__init__(self, **kwargs)
        API.__init__(self)

    def _build_session(self, **kwargs: Any) -> None:
        APISession._build_session(self, **kwargs)
        self._session.headers.update({"User-Agent": "Python/onboardapis (%s)" % get_package_version()})


class ThreadedRestAPI(ThreadedAPI, BlockingRestAPI, metaclass=ABCMeta):
    """A threaded version of the ``BlockingRestAPI``."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a new ``ThreadedRestAPI``."""
        kwargs['url'] = kwargs.pop('url', self.API_URL)
        APISession.__init__(self, **kwargs)
        ThreadedAPI.__init__(self)


class BlockingGraphQlAPI(Client, API):
    """A GraphQL ``API`` that uses a ``gql.client.Client`` to fetch data."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a new ``BlockingGraphQlAPI``.

        Args:
            kwargs: The kwargs to pass to the underlying ``gql.client.Client``.
        """
        kwargs.update({
            'transport': kwargs.pop('transport', RequestsHTTPTransport(
                url=self.API_URL,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Python/onboardapis (%s)' % get_package_version(),
                },
            )),
            'fetch_schema_from_transport': kwargs.pop('fetch_schema_from_transport', True),
        })
        Client.__init__(self, **kwargs)
        API.__init__(self)


class ThreadedGraphQlAPI(BlockingGraphQlAPI, ThreadedAPI, metaclass=ABCMeta):
    """A threaded version of the ``BlockingGraphQlAPI``."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a new ``ThreadedGraphQlAPI``.

        Args:
            kwargs: The kwargs to pass to the underlying ``gql.client.Client``.
        """
        BlockingGraphQlAPI.__init__(self, **kwargs)
        ThreadedAPI.__init__(self)
