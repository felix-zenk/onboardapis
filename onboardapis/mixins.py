"""
Mixins for vehicles.

The mixins are used to indicate and add functionality to the vehicle classes.
"""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import timedelta
from typing import Generic

from .exceptions import DataInvalidError
from .data import Position, InternetAccessInterface, ID, StationType, API
from . import Station


class PositionMixin(metaclass=ABCMeta):
    @property
    @abstractmethod
    def position(self) -> Position:
        """
        Get the current position of the vehicle.

        :return: The current position of the vehicle
        :rtype: Position
        """
        raise NotImplementedError


class SpeedMixin(metaclass=ABCMeta):
    """
    Functionality for a vehicle that provides information about its speed.
    """

    @property
    @abstractmethod
    def speed(self) -> float:
        """The current speed of the vehicle.

        Returns:
            The current speed in \\frac{meters}{second}
        """
        raise NotImplementedError


class StationsMixin(Generic[StationType], metaclass=ABCMeta):
    """
    Functionality for a vehicle that provides information on the journey.
    """

    def calculate_distance(self, station: Station) -> float:
        """Calculate the distance in meters between the train and a station.

        Use the trains ``position`` or ``distance`` to calculate the distance to ``station``.

        Args:
            station: The station to calculate the distance to

        Returns:
            The distance between the train and the station in meters
        """
        if hasattr(self, 'position'):
            position: Position = getattr(self, 'position')
            return station.calculate_distance(position)

        if hasattr(self, 'distance'):
            distance: float = getattr(self, 'distance')
            return station.calculate_distance(distance)

        raise NotImplementedError

    @property
    @abstractmethod
    def stations_dict(self) -> dict[ID, StationType]:
        """A dict containing the stations on the journey.

        The stations that this vehicle passes through returned as a dict with the station ID as the key.

        Returns:
            The stations as a dict
        """
        raise NotImplementedError

    @property
    def stations(self) -> list[StationType]:
        """Return the stations as a list.

        Return a list that contains every station from `onboardapis.mixins.StationsMixin.stations_dict`.

        Returns:
            The `stations_dict` values
        """
        return list(self.stations_dict.values())

    @property
    def origin(self) -> StationType:
        """The station where this vehicle started the current journey.

        Returns:
            The first station on this trip.
        """
        if len(self.stations) > 0:
            return self.stations[0]
        raise DataInvalidError("No origin station found")

    @property
    @abstractmethod
    def current_station(self) -> StationType:
        """The next station.

        Returns:
            The station where this vehicle will arrive next or is currently at.
        """
        raise NotImplementedError

    @property
    def destination(self) -> StationType:
        """The station where this vehicle terminates the current journey.

        Returns:
            The destination station.
        """
        if len(self.stations) > 0:
            return self.stations[-1]
        raise DataInvalidError("No destination station found")

    @property
    def delay(self) -> timedelta:
        """The current delay.

        The current delay calculated by the `current_station`
        scheduled arrival time vs. actual arrival time.

        Returns:
            The current delay of the vehicle as a `datetime.timedelta` object.
        """
        return timedelta(seconds=(
            self.current_station.arrival.actual - self.current_station.arrival.scheduled
        ).total_seconds())

    @property
    def distance(self) -> float:
        """
        The distance from the start in meters

        :return: The distance
        :rtype: float
        """
        return self.calculate_distance(self.origin)


class InternetAccessMixin(metaclass=ABCMeta):
    _internet_access: InternetAccessInterface

    @property
    def internet_access(self) -> InternetAccessInterface:
        """An interface to enable or disable the internet access for this device."""
        return self._internet_access
