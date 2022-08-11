import abc
import json
import threading
import time

import requests

from typing import Any, Optional

from ..exceptions import DataInvalidError
from .. import __version__


def some_or_default(data: Any, default: Any = None) -> Optional[Any]:
    """
     Return ``data`` if there is actually some content in data, else return ``default`` \
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


class DataStorage:
    """
    A storage class that can be used to store data and retrieve it later.
    """

    __slots__ = []

    def get(self, key: str) -> Any:
        return getattr(self, key)

    def set(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def remove(self, key: str) -> None:
        delattr(self, key)

    def items(self):
        return vars(self).items()


class DataConnector(metaclass=abc.ABCMeta):
    """
    A class for retrieving data from an API
    """

    __slots__ = ["base_url", "_session", "_cache", "_verify"]

    def __init__(self, base_url: str, verify: bool = True):
        """
        Initialize a new :class:`DataConnector`

        :param base_url: The base url of the server to connect to
        """
        self.base_url = base_url
        self._session = requests.Session()
        self._cache = DataStorage()
        self._verify = verify

    def _get(self, endpoint, *args, **kwargs):
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
        except (AttributeError, KeyError):
            return __default

    def store(self, key, value):
        self._cache.set(key, value)

    @abc.abstractmethod
    def refresh(self):  # pragma: no cover
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

    __slots__ = ["_runner", "_running", "_initialized"]

    def __init__(self, base_url: str, *args, **kwargs):
        super().__init__(base_url, *args, **kwargs)
        self._runner = threading.Thread(target=self.run, name=f"DataConnector Runner for '{base_url}'", daemon=True)
        self._running = False
        self._initialized = False

    def run(self) -> None:
        """
        The main loop to run in a separate thread
        """
        tps = 20  # 20 ticks per second -> check for thread join every 0.05 seconds, refresh each second
        counter = 0
        while self._running:
            if counter == 0:
                self.refresh()
                if not self._initialized:
                    self._initialized = True
            time.sleep(1 / tps)
            counter = (counter + 1) % tps

    def start(self) -> None:
        """
        Start requesting data
        """
        self._running = True
        self._runner.start()
        while not self._initialized:  # pragma: no cover
            # Wait until the new thread has initialized (received data at least once)
            pass

    def stop(self):
        """
        Stop requesting data
        """
        self._running = False
        if self._runner.is_alive():
            self._runner.join(2)

    def reset(self):
        """
        Reset the thread and the cache so that they can be reused with ``start()``
        """
        self.stop()
        self._runner = threading.Thread(
            target=self.run, name=f"DataConnector Runner for '{self.base_url}'", daemon=True
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

    def _get(self, endpoint, *args, **kwargs):
        headers = kwargs.get("headers", {})
        headers.update({
            "accept": "application/json",
        })
        try:
            return super(JSONDataConnector, self)._get(endpoint, *args, **kwargs).json()
        except json.JSONDecodeError as e:
            raise DataInvalidError() from e
