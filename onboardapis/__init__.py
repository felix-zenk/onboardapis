"""
# What is onboardapis?

onboardapis is a Python library that provides a unified interface to the APIs of public transport providers.

# How does it work?

onboardapis provides a common interface for all public transport providers. This interface is defined by the
`onboardapis.Vehicle` class. This class provides a common interface for all vehicles, regardless of the API they are
implemented in. The `onboardapis.Vehicle` is subclassed by `onboardapis.train.Train`, `onboardapis.bus.Bus`,
`onboardapis.plane.Plane` and `onboardapis.ship.Ship` which
provide a common interface for all vehicles of that type. These classes are then subclassed by the actual API
implementations. For example, the `onboardapis.train.de.db.ICEPortal` class provides a common interface
for all trains of the Deutsche Bahn that provide access to the ICE Portal.

# How do I install it?

To use onboardapis, you need to install it first. You can do this by running the following command:

```bash
$ python3 -m pip install onboardapis
```

or if you are on Windows and have the py launcher installed:

```shell
> py -m pip install onboardapis
```

After that, you can use onboardapis in your project by importing it:

```python
import onboardapis
```

Development versions can be installed directly from GitHub:

```bash
$ python3 -m pip install git+https://github.com/felix-zenk/onboardapis
```

# How do I get started?

To get started, you need to follow the package structure of onboardapis.
The structure is in the format of `onboardapis.<vehicle-type>.<country-code>.<operator-id>`.
You will find the API implementations for that operator in this package.
A single operator may have multiple APIs,
for example the Deutsche Bahn has the `onboardapis.train.de.db.ICEPortal` and the `onboardapis.train.de.db.ZugPortal`.

The vehicle type is one of **train**, **bus**, **plane** or **ship**.
The country code is the
[ISO 3166-1 alpha-2 code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements)
of the country the operator is based in.
The operator ID is a unique identifier for the operator and depends on the vehicle type.
"""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from ._types import ID
from .data import DataConnector, ThreadedDataConnector, ScheduledEvent, Position
from .exceptions import NotImplementedInAPIError


class Vehicle(metaclass=ABCMeta):
    """
    Base class for all vehicles
    """

    _data: DataConnector
    """The :class:`DataConnector` that supplies the data for this vehicle"""

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def init(self) -> None:
        """Initialize the connection to the API.

        Call the init method of the DataConnector that supplies the data for this vehicle.

        Raises:
          InitialConnectionError: If the connection to the API could not be established.
        """
        if isinstance(self._data, ThreadedDataConnector):
            self._data.start()
            while not self._data.connected:
                pass
            return

        raise NotImplementedError

    def shutdown(self) -> None:
        """
        This method will be called when exiting the context manager and can be overwritten by subclasses.

        :return: Nothing
        :rtype: None
        """
        pass

    def now(self) -> datetime:
        """
        Get the current time as seen by the vehicle

        :return: The current time
        :rtype: datetime.datetime
        """
        return datetime.now()

    @property
    @abstractmethod
    def id(self) -> ID:
        """
        The unique ID of this specific vehicle

        :return: The ID
        :rtype: str
        """
        raise NotImplementedInAPIError


@dataclass
class ConnectingVehicle(object):
    """
    A connecting vehicle is a vehicle that is not part of the main trip but of a connecting service.
    It may only have limited information available.
    """
    vehicle_type: str | None
    """The abbreviated vehicle type"""
    line_number: str | None
    """The line number of the vehicle"""
    departure: ScheduledEvent[datetime] | None
    """The departure time of the vehicle"""
    destination: str | None
    """The destination of the vehicle"""


@dataclass
class Station(object):
    """
    A Station is a stop on the trip
    """
    id: ID
    """The ID of the station"""
    name: str
    """The name of the station"""
    arrival: ScheduledEvent[datetime] | None
    """The arrival time at this station"""
    departure: ScheduledEvent[datetime] | None
    """The departure time from this station"""
    position: Position | None
    """The geographic position of the station"""
    distance: float | None
    """The distance from the start to this station"""
    _connections: Iterable[ConnectingVehicle]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    def __str__(self) -> str:
        return self.name

    @property
    def connections(self) -> list[ConnectingVehicle]:
        """The connecting services departing from this station."""
        if not isinstance(self._connections, list):
            self._connections = list(self._connections)
        return self._connections

    def calculate_distance(self, other: Station | Position | int | float) -> float | None:
        """
        Calculate the distance in meters between this station and something else.

        Accepts a :class:`Station`, :class:`Position` or a number for the distance calculation.

        :param other: The other station or position to calculate the distance to
        :type other: Station | Position | int | float
        :return: The distance in meters
        :rtype: Optional[float]
        """
        # If there is not enough information to calculate the distance, return None
        if other is None:
            return None

        # Both distances since the start are known
        if isinstance(other, (int, float)) and self.distance is not None:
            return (
                other - self.distance
                if self.distance - other < 0
                else self.distance - other
            )

        # Both positions are known
        if isinstance(other, Position) and self.position is not None:
            return self.position.calculate_distance(other)

        # Both are a station
        if isinstance(other, Station):
            if self.distance is not None and other.distance is not None:
                return (
                    other.distance - self.distance
                    if self.distance - other.distance < 0
                    else self.distance - other.distance
                )
            if self.position is not None and other.position is not None:
                return self.position.calculate_distance(other.position)
