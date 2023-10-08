"""
This module contains everything that has to do with data and data management
"""
from __future__ import annotations

import json
import logging
import threading
import time
import requests

from os import PathLike
from abc import ABCMeta, abstractmethod
from typing import Any, Optional, TypeVar, Generic, ItemsView, Union, Sequence
from requests import Response, RequestException

from geopy.point import Point
from geopy.distance import geodesic

from .conversions import coordinates_decimal_to_dms
from .exceptions import DataInvalidError, APIConnectionError, InitialConnectionError
from . import __version__


def some_or_default(
    data: Optional[Any], default: Optional[Any] = None
) -> Optional[Any]:
    """
    Return ``data`` if there is actually some content in data, else return ``default``.

    Useful when data such as "" or b'' should also be treated as empty.

    :param data: The data to test
    :type data: Any
    :param default: The default value to return if no data is present
    :type default: Any
    :return: The data if present, else the default
    :rtype: Optional[Any]
    """
    if data is None:
        return default
    if isinstance(data, str) and data == "":
        return default
    if isinstance(data, bytes) and data == b"":
        return default
    # if isinstance(data, Sized) and len(data) == 0:
    #     return default
    return data


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
        :type scheduled: Optional[T]
        :param actual: The value that actually happens
        :type actual: Optional[T]
        """
        self.scheduled = scheduled
        """
        The expected value of this event
        """
        self.actual = actual  # TODO scheduled as default?
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


class DataStorage:
    """
    A storage class that can be used to store data and retrieve it later.
    """

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.set(key, value)

    def get(self, key: str) -> Any:
        """
        Get the value of the given key out of the storage.

        Raises an :class:`AttributeError` if the key is not present.

        :param key: The key to get the value of
        :type key: str
        :return: The stored value
        :rtype: Any
        """
        return getattr(self, key)

    def set(self, key: str, value: Any) -> None:
        """
        Set the value of the given key in the storage.

        Overwrites existing keys.

        :param key: The key to set the value of
        :type key: str
        :param value: The value to store
        :type value: Any
        :return: Nothing
        :rtype: None
        """
        setattr(self, key, value)

    def remove(self, key: str) -> None:
        """
        Remove the given key and its value from the storage.

        :param key: The key to remove
        :type key: str
        :return: Nothing
        :rtype: None
        """
        delattr(self, key)

    def items(self) -> ItemsView[str, Any]:
        """
        Get all keys and values from the storage.

        :return: A view of all keys and values
        :rtype: ItemsView[str, Any]
        """
        return vars(self).items()


class APIConnector(metaclass=ABCMeta):
    API_URL: str

    @abstractmethod
    def static_refresh(self):
        pass

    @abstractmethod
    def dynamic_refresh(self):
        pass


class DataConnector(metaclass=ABCMeta):
    """
    A class for retrieving data from an API
    """

    API_URL: str
    """
    The API URL this DataConnector points to
    """

    __slots__ = ["API_URL", "_session", "_cache", "_retries"]

    def __init__(self) -> None:
        """
        Initialize a new :class:`DataConnector`
        """
        self._session = requests.Session()
        self._cache = DataStorage()
        self._retries = 0

    def __del__(self):
        self._session.close()

    def _get(
        self, endpoint: str, *args: Any, base_url: str = None, **kwargs: Any
    ) -> Response:
        """
        Request data from the server.

        :param str endpoint: The endpoint to request data from
        :param Any args: args to pass to the request
        :param str base_url: An optional different base url to use for the request
        :param Any kwargs: kwargs to pass to the request
        :return: The response from the server
        :rtype: Response
        """
        # Overwrite some kwargs
        kwargs |= {
            "headers": kwargs.get("headers", {})
            | {"user-agent": f"python-onboardapis/{__version__}"},
            "timeout": 1,
            "verify": bool(kwargs.get("verify", "True")),
        }
        # Allow a different base url, but use self.base_url as default
        base_url = self.API_URL if base_url is None else base_url
        try:
            response = self._session.get(
                f"https://{base_url}{endpoint}", *args, **kwargs
            )
            response.raise_for_status()
            # Report possible errors / changes in the API
            if not response.ok:
                logging.getLogger(__name__).warning(
                    f"Request to https://{base_url}{endpoint} returned status code {response.status_code}"
                )
            self._retries = 0
            return response
        except RequestException as e:
            # If the request failed 3 times in a row, raise an error
            if self._retries > 2:
                raise APIConnectionError() from e
            # Retry the request if it failed
            self._retries += 1
            logging.getLogger(__name__).debug(
                f"Request to https://{base_url}{endpoint} failed! Retry: ({self._retries}/2)"
            )
            return self._get(endpoint, *args, base_url=base_url, **kwargs)

    def load(self, key: str, __default: Any = None) -> Any:
        """
        Load data from the cache

        :param key: The key to load
        :param __default: The default value to return if the key is not present
        :return: The data if present, else the default
        """
        try:
            return self._cache.get(key)
        except AttributeError:
            return __default

    def store(self, key: str, value: Any) -> None:
        """
        Store data in the cache

        :param key: The key the data should be stored under
        :param value: The data to store
        :return: Nothing
        """
        self._cache.set(key, value)

    @abstractmethod
    def refresh(self) -> None:  # pragma: no cover
        """
        Method that collects data from the server and stores it in the cache

        :return: Nothing
        """
        pass


class StaticDataConnector(DataConnector, metaclass=ABCMeta):
    """
    A :class:`DataConnector` for data never changes and therefore has to be requested only once
    """

    # Maybe add additional functionality over DataConnector?

    __slots__ = []


class DynamicDataConnector(DataConnector, metaclass=ABCMeta):
    """
    A :class:`DataConnector` for data that changes frequently and therefore has to be requested continuously
    """

    __slots__ = ["_runner", "_running", "_initialized", "optimize", "silent"]

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._runner = threading.Thread(
            target=self._run,
            name=f"DynamicDataConnector-Runner for '{self.API_URL}'",
            daemon=True,
        )
        self._running = False
        self._initialized = False

    @property
    def connected(self) -> bool:
        """
        Check whether the connector is connected to the server
        """
        return self._initialized and self._running

    def _run(self) -> None:
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

            # If optimize is enabled, measure the time it took to refresh the data
            # and calculate the remaining ticks until target time
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
        self._runner = threading.Thread(
            target=self._run,
            name=f"DynamicDataConnector-Runner for '{self.API_URL}'",
            daemon=True,
        )
        self._session = requests.Session()
        self._cache = DataStorage()
        self._initialized = False


class JSONDataConnector(DataConnector, metaclass=ABCMeta):
    """
    A :class:`DataConnector` that automatically parses the response to a json object
    """

    __slots__ = []

    def _get(self, endpoint: str, *args: Any, **kwargs: Any) -> dict:
        kwargs["headers"] = kwargs.get("headers", {}) | {"accept": "application/json"}
        try:
            return super(JSONDataConnector, self)._get(endpoint, *args, **kwargs).json()
        except json.JSONDecodeError as e:
            logging.getLogger(__name__).debug(
                f"Failed to parse json ({e.__class__.__name__}): {'; '.join(e.args)}"
            )
            raise DataInvalidError() from e

    def export(self, path: Union[str, PathLike], keys: Sequence = None) -> None:
        """
        Export the cache to a json file

        :param Union[str, PathLike] path: The path to export to
        :param Sequence keys: The specific keys to export, if empty export all keys
        :return: Nothing
        :rtype: None
        """
        data = {}
        for key, value in self._cache.items():
            if keys is None:
                data[key] = value
            # assume keys is Sequence
            elif key in keys:
                data[key] = value
            # else pass

        if not str(path).endswith(".json"):
            path = f"{path}.json"

        with open(path, "w") as f:
            json.dump(data, f, default=lambda o: o.__dict__)


class GraphQLDataConnector(DataConnector, metaclass=ABCMeta):
    pass


class WebsocketDataConnector(DataConnector, metaclass=ABCMeta):
    pass


class DummyDataConnector(StaticDataConnector, DynamicDataConnector):
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
