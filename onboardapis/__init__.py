"""
.. include:: ../README.md

---
"""
from __future__ import annotations

import logging

from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from time import sleep
from typing import Iterable

from .data import ID, API, ThreadedAPI, ScheduledEvent, Position

logger = logging.getLogger(__name__)

__all__ = [
    "bus",
    "data",
    "exceptions",
    "mixins",
    "other",
    "plane",
    "protocols",
    "ship",
    "train",
    "units",
    "Vehicle",
    "Station",
    "ConnectingVehicle",
]


class Vehicle(metaclass=ABCMeta):
    """
    Base class for all vehicles
    """

    _api: API
    """The :class:`API` that supplies the data for this vehicle."""

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def init(self) -> None:
        """Initialize the connection to the API.

        Call the init method of the API that supplies the data for this vehicle.

        Raises:
          InitialConnectionError: If the connection to the API could not be established.
        """
        if not hasattr(self, '_api'):
            return  # Abstract class without API implementation

        if isinstance(self._api, ThreadedAPI):
            self._api.start()
            while not self._api.is_connected:
                sleep(.1)
            return

        return

    def shutdown(self) -> None:
        """
        This method will be called when exiting the context manager and can be overwritten by subclasses.

        :return: Nothing
        :rtype: None
        """
        pass

    @property
    def now(self) -> datetime:
        """
        Get the current time as seen by the vehicle

        :return: The current time
        :rtype: datetime.datetime
        """
        return datetime.now()

    @property
    def id(self) -> ID:
        """The unique ID of this specific vehicle."""
        return 'undefined'


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
            return abs(self.distance - other)

        # Both positions are known
        if isinstance(other, Position) and self.position is not None:
            return self.position.calculate_distance(other)

        # Both are a station
        if isinstance(other, Station):
            if self.distance is not None and other.distance is not None:
                return abs(self.distance - other.distance)
            if self.position is not None and other.position is not None:
                return self.position.calculate_distance(other.position)
