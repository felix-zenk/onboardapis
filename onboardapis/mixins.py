from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

from .exceptions import DataInvalidError
from .data import Position
from .types import ID
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
    @property
    @abstractmethod
    def speed(self) -> float:
        """
        Get the current speed of the vehicle.

        :return: The current speed of the vehicle
        :rtype: float
        """
        raise NotImplementedError


StationType = TypeVar("StationType", bound=Station)


class StationsMixin(Generic[StationType], metaclass=ABCMeta):
    @property
    @abstractmethod
    def stations_dict(self) -> dict[ID, StationType]:
        """
        The stations that this vehicle passes through returned as a dict with the station ID as the key.
        Mostly ID will be of type str.

        :return: The stations as a dict with
        :rtype: Dict[str, StationType]
        """
        pass

    @property
    def stations(self) -> list[StationType]:
        """
        Return the stations as a list

        :rtype: List[StationType]
        """
        return list(self.stations_dict.values())

    @property
    def origin(self) -> StationType:
        """
        The station where this vehicle started the current journey

        :return: The first station on this trip
        :rtype: StationType
        """
        if len(self.stations) > 0:
            return self.stations[0]
        raise DataInvalidError("No origin station found")

    @property
    @abstractmethod
    def current_station(self) -> StationType:
        """
        The station where this vehicle will arrive next or is currently at

        :return: The current station
        :rtype: StationType
        """
        # Get the current station id
        # Get the station from the stations dict
        pass

    @property
    def destination(self) -> StationType:
        """
        The station where this vehicle will end the current journey

        :return: The last station on this trip
        :rtype: StationType
        """
        if len(self.stations) > 0:
            return self.stations[-1]
        raise DataInvalidError("No destination station found")

    @property
    def delay(self) -> float:
        """
        The current delay of the vehicle in seconds

        :return: The delay of the vehicle
        :rtype: float
        """
        return (
            self.current_station.arrival.actual - self.current_station.arrival.scheduled
        ).total_seconds()
