"""
Package metadata and base classes.
"""

from __future__ import annotations

__version_info__ = (2, 0, 0)
__version__ = ".".join(map(str, __version_info__))

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, NoReturn

from ._types import ID
from .data import DataConnector, PollingDataConnector, ScheduledEvent, Position
from .exceptions import NotImplementedInAPIError


class API(object):
    """
    Base class for all APIs
    """


class Vehicle(API, metaclass=ABCMeta):
    """
    The base class for all vehicles.
    """

    _data: DataConnector
    """The :class:`DataConnector` that supplies the data for this vehicle"""

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def init(self) -> None:
        """
        Initialize the :class:`DataConnector`.

        :return: Nothing
        :rtype: None
        """
        if isinstance(self._data, PollingDataConnector):
            self._data.start()
            while not self._data.connected:
                pass
            return

        raise NotImplementedError

    def shutdown(self) -> None:
        """
        Method to call when exiting the context manager

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
        pass


@dataclass
class ConnectingVehicle(object):
    """
    A connecting vehicle is a vehicle that is not part of the main trip but of a connecting service

    It may only have limited information available
    """

    vehicle_type: str | None
    """
    The abbreviated vehicle type
    """
    line_number: str | None
    """
    The line number of the vehicle
    """
    departure: ScheduledEvent[datetime] | None
    """
    The departure time of the vehicle
    """
    destination: str | None
    """
    The destination of the vehicle
    """


class IncompleteVehicleMixin(Vehicle, metaclass=ABCMeta):
    """
    Base class for mixins that implement the abstract methods of their bases
    if the API does not provide the requested data.
    """

    @property
    def id(self) -> NoReturn:
        raise NotImplementedInAPIError


class Station(object):
    """
    A Station is a stop on the trip
    """

    __slots__ = (
        "_id",
        "_name",
        "_arrival",
        "_departure",
        "_position",
        "_distance",
        "_connections",
    )

    def __init__(
        self,
        station_id: ID,
        name: str,
        arrival: ScheduledEvent[datetime] = None,
        departure: ScheduledEvent[datetime] = None,
        position: Position = None,
        distance: float = None,
        connections: Iterable[ConnectingVehicle] = None,
    ):
        """
        Initialize a new :class:`Station`

        :param station_id: The ID of the station
        :type station_id: Any
        :param name: The name of the station
        :type name: str
        :param arrival: The arrival time at this station
        :type arrival: ScheduledEvent[datetime.datetime]
        :param departure: The departure time from this station
        :type departure: ScheduledEvent[datetime.datetime]
        :param position: The geographic position of the station
        :type position: Position
        :param distance: The distance from the start to this station
        :type distance: float
        :param connections: The connecting services departing from this station
        :type connections: Iterable[ConnectingVehicle]
        """
        self._id = station_id
        self._name = name
        self._arrival = arrival
        self._departure = departure
        self._position = position
        self._distance = distance
        self._connections = connections

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    def __str__(self) -> str:
        return self.name

    @property
    def id(self) -> ID:
        """
        The unique ID of the station

        :return: The ID of the station
        :rtype: Any
        """
        return self._id

    @property
    def name(self) -> str:
        """
        The name of the station

        :return: The name of the station
        :rtype: str
        """
        return self._name

    @property
    def arrival(self) -> ScheduledEvent[datetime]:
        """
        The arrival time at this station

        :return: The datetime object of the arrival time encased in a ScheduledEvent
        :rtype: ScheduledEvent[datetime.datetime]
        """
        return self._arrival

    @property
    def departure(self) -> ScheduledEvent[datetime]:
        """
        The departure time at this station

        :return: The datetime object of the departure time encased in a ScheduledEvent
        :rtype: ScheduledEvent[datetime.datetime]
        """
        return self._departure

    @property
    def connections(self) -> list[ConnectingVehicle]:
        """
        The connecting services departing from this station

        :return: A list of ConnectingVehicle objects
        :rtype: list[ConnectingVehicle]
        """
        # run generator or return cached list
        if not isinstance(self._connections, list):
            self._connections = list(self._connections)
        return self._connections

    @property
    def distance(self) -> float:
        """
        The distance from the start to this station in meters

        :return: The distance
        :rtype: float
        """
        return self._distance

    @property
    def position(self) -> Position:
        """
        The geographic position of the station

        :return: The coordinates of the station
        :rtype: Position
        """
        return self._position

    def calculate_distance(
        self, other: Station | Position | int | float
    ) -> float | None:
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
