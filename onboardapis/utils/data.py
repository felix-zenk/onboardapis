"""
This module contains everything that has to do with data and data management
"""

import abc
import json
import threading
import time

import requests

from typing import Any, Optional, TypeVar, Generic, ItemsView

from requests import Response

from ..exceptions import DataInvalidError, APIConnectionError, InitialConnectionError
from .. import __version__


def some_or_default(data: Optional[Any], default: Optional[Any] = None) -> Optional[Any]:
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


T = TypeVar('T')
"""
A type variable for generic functions
"""


class ScheduledEvent(Generic[T]):
    """
    Something that is scheduled and can happen as ``scheduled``,
    but can also happen different from the expected and actually happens as ``actual``
    """

    __slots__ = ["scheduled", "actual"]

    def __init__(self, scheduled: Optional[T] = None, actual: Optional[T] = None):
        """
        Initialize a new :class:`ScheduledEvent`

        :param scheduled: The value that should happen
        :type scheduled: Optional[T]
        :param actual: The value that actually happens
        :type actual: Optional[T]
        """
        self.scheduled = scheduled
        self.actual = actual

    def __repr__(self):
        if self.actual is None:
            return f"<{self.__class__.__name__} {self.scheduled}>"
        return f"<{self.__class__.__name__} {self.actual}>"

    def __str__(self):
        if self.actual is None:
            return f"{self.scheduled}"
        return f"{self.actual}"


class DataStorage:
    """
    A storage class that can be used to store data and retrieve it later.
    """

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


class DataConnector(metaclass=abc.ABCMeta):
    """
    A class for retrieving data from an API
    """

    __slots__ = ["base_url", "_session", "_cache", "_verify"]

    def __init__(self, base_url: str, *, verify: bool = True) -> None:
        """
        Initialize a new :class:`DataConnector`

        :param base_url: The base url of the server to connect to
        :type base_url: str
        :param verify: Whether to verify the TLS certificate of the server
        :type verify: bool
        """
        self.base_url = base_url
        self._session = requests.Session()
        self._cache = DataStorage()
        self._verify = verify

    def __del__(self):
        self._session.close()

    def _get(self, endpoint: str, *args: Any, **kwargs: Any) -> Response:
        """
        Request data from the server

        :param endpoint: The endpoint to request data from
        :type endpoint: str
        :param args: args to pass to the request
        :type args: Any
        :param kwargs: kwargs to pass to the request
        :type kwargs: Any
        :return: The response from the server
        :rtype: Response
        """
        # Overwrite some kwargs
        headers = kwargs.get("headers", {})
        headers.update({
            "user-agent": f"python-onboardapis/{__version__}"
        })
        kwargs.update({
            "headers": headers,
            "timeout": 1,
            "verify": kwargs.get("verify", self._verify)
        })
        return self._session.get(f"https://{self.base_url}{endpoint}", *args, **kwargs)

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

    @abc.abstractmethod
    def refresh(self) -> None:  # pragma: no cover
        """
        Method that collects data from the server and stores it in the cache

        :return: Nothing
        """
        pass


class StaticDataConnector(DataConnector, metaclass=abc.ABCMeta):
    """
    A :class:`DataConnector` for data never changes and therefore has to be requested only once
    """

    __slots__ = []

    def __init__(self, base_url: str, *args, **kwargs):
        super().__init__(base_url, *args, **kwargs)


class DynamicDataConnector(DataConnector, metaclass=abc.ABCMeta):
    """
    A :class:`DataConnector` for data that changes frequently and therefore has to be requested continuously
    """

    __slots__ = ["_runner", "_running", "_initialized", "optimize"]

    def __init__(self, base_url: str, *args, **kwargs):
        super().__init__(base_url, *args, **kwargs)
        self._runner = threading.Thread(
            target=self._run, name=f"DynamicDataConnector-Runner for '{self.base_url}'", daemon=True
        )
        self._running = False
        self._initialized = False
        self.optimize = True

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
                raise e

            # Signal that the data has been refreshed at least once (for thread synchronization)
            if not self._initialized:
                self._initialized = True

            # If optimize is enabled, measure the time it took to refresh the data
            # and calculate the remaining ticks until target time
            if self.optimize:
                counter = (tps - int(max(0.0, (target - time.time_ns()) / 1e9) * tps)) % tps
            else:
                counter = (counter + 1) % tps

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
            raise InitialConnectionError("Failed to connect to the server")

    def stop(self):
        """
        Stop requesting data and shut down the separate thread
        """
        self._running = False
        if self._runner.is_alive():
            self._runner.join()

    def reset(self):
        """
        Reset the thread and the cache so that they can be reused with ``start()``
        """
        self.stop()
        self._runner = threading.Thread(
            target=self._run, name=f"DynamicDataConnector-Runner for '{self.base_url}'", daemon=True
        )
        self._session = requests.Session()
        self._cache = DataStorage()
        self._running = False
        self._initialized = False


class JSONDataConnector(DataConnector, metaclass=abc.ABCMeta):
    """
    A :class:`DataConnector` that automatically parses the response to a json object
    """

    __slots__ = []

    def _get(self, endpoint: str, *args: Any, **kwargs: Any) -> dict:
        headers = kwargs.get("headers", {})
        headers.update({
            "accept": "application/json",
        })
        try:
            return super(JSONDataConnector, self)._get(endpoint, *args, **kwargs).json()
        except json.JSONDecodeError as e:
            raise DataInvalidError() from e
