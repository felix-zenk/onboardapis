"""
Mixins for vehicles.

The mixins are used to indicate and add functionality to the vehicle classes.
"""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from datetime import timedelta
from typing import Generic

from .exceptions import DataInvalidError
from .data import Position, ID, StationType, API


class PositionMixin(metaclass=ABCMeta):
    @property
    @abstractmethod
    def position(self) -> Position:
        """
        :return: The current position of the vehicle
        :raises DataInvalidError: If the position could not be fetched from the server
        """
        raise NotImplementedError


class SpeedMixin(metaclass=ABCMeta):
    """
    Functionality for a vehicle that provides information about its speed.
    """

    @property
    @abstractmethod
    def speed(self) -> float:
        r"""
        :return: The current speed of the vehicle in $\frac{meters}{second}$
        :raises DataInvalidError: If the speed could not be fetched from the server
        """
        raise NotImplementedError


class StationsMixin(Generic[StationType], metaclass=ABCMeta):
    """
    Functionality for a vehicle that provides information on the journey.
    """

    def calculate_distance(self, station: StationType) -> float:
        """
        :return: The distance in meters between the vehicle and a station
        :param station: The station to calculate the distance to
        :raises DataInvalidError: If the distance between the vehicle and the station could not be calculated
                                  due to missing information from the server
        :raises NotImplementedError: If the vehicle does not implement ``position`` or ``distance``
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
        """
        :return: The stations as a dict of station ID to station instance
        :raises DataInvalidError: If the stations could not be fetched from the server
        """
        raise NotImplementedError

    @property
    def stations(self) -> list[StationType]:
        """
        :return: A list that contains every station from `onboardapis.mixins.StationsMixin.stations_dict`.
        :raises DataInvalidError: If the stations could not be fetched from the server
        """
        return list(self.stations_dict.values())

    @property
    def origin(self) -> StationType:
        """
        :return: The first station on this trip.
        :raises DataInvalidError: If the origin station could not be fetched from the server
        """
        if len(self.stations) > 0:
            return self.stations[0]
        raise DataInvalidError("No origin station found!")

    @property
    @abstractmethod
    def current_station(self) -> StationType:
        """
        :return: The station where this vehicle will arrive next or is currently at
        :raises DataInvalidError: If the current station could not be fetched from the server
        """
        raise NotImplementedError

    @property
    def destination(self) -> StationType:
        """
        :return: The station where this vehicle terminates the current journey
        :raises DataInvalidError: If the destination station could not be fetched from the server
        """
        if len(self.stations) > 0:
            return self.stations[-1]
        raise DataInvalidError("No destination station found!")

    @property
    def delay(self) -> timedelta:
        """
        :return: The current delay of the vehicle as a `datetime.timedelta` object.
        :raises DataInvalidError: If the delay could not be fetched from the server
        """
        return timedelta(seconds=(
            self.current_station.arrival.actual - self.current_station.arrival.scheduled
        ).total_seconds())

    @property
    def is_delayed(self) -> bool:
        """
        :returns: Whether ``delay`` `> timedelta(seconds=0)`
        :raises DataInvalidError: If the delay could not be fetched from the server
        """
        return self.delay > timedelta()

    @property
    def distance(self) -> float:
        """
        :return: The distance from the start in meters
        :raises DataInvalidError: If the distance could not be fetched from the server
        """
        return self.calculate_distance(self.origin)


class InternetAccessMixin(metaclass=ABCMeta):
    """Adds the internet_access property to a class
    that defines an :class:`InternetAccessInterface` as ``_internet_access``."""
    _internet_access: InternetAccessInterface

    @property
    def internet_access(self) -> InternetAccessInterface:
        """
        :return: An interface to manage the internet access for this device
        """
        return self._internet_access


class InternetAccessInterface(metaclass=ABCMeta):
    """Interface adding functions for connecting and disconnecting to the internet
    as well as viewing the current status."""

    _is_enabled: bool = False
    """Cached information on connection status"""
    _api: API

    def __init__(self, api: API) -> None:
        self._api = api

    @abstractmethod
    def enable(self) -> None:
        """Enable the internet access for this device.

        **IMPORTANT**:
            By using this method you automatically agree to the terms of service of the internet access provider.

        :raises ConnectionError: If the internet access is (temporarily) not available.
        """
        self._is_enabled = True

    @abstractmethod
    def disable(self) -> None:
        """Disable the internet access for this device.

        Disable the internet access for this device by signing out of the captive portal.

        :raises ConnectionError: If the internet access is (temporarily) not available.
        """
        if not self.is_enabled:
            return

        self._is_enabled = False

    @property
    def is_enabled(self) -> bool:
        """
        :return: Whether the internet access is enabled for this device
        """
        return self._is_enabled


class InternetMetricsInterface(metaclass=ABCMeta):
    """Interface for information on limited internet access."""

    @property
    @abstractmethod
    def limit(self) -> int | float | None:
        """
        :return: The total internet access quota in MB or `None` if there is none
        :raises DataInvalidError: If the quota could not be fetched from the server
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def used(self) -> int | float | None:
        """
        :return: The amount used of the quota in MB or `None` if there is none
        :raises DataInvalidError: If the usage information could not be fetched from the server
        """
        raise NotImplementedError
