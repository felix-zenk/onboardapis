"""
Abstract base classes for train
"""
from __future__ import annotations
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import datetime
from dataclasses import dataclass
from typing import Iterable, NoReturn
from abc import ABCMeta, abstractmethod

from .. import Vehicle, IncompleteVehicleMixin, Station, ConnectingVehicle
from ..mixins import PositionMixin, SpeedMixin, StationsMixin
from ..exceptions import NotImplementedInAPIError
from ..data import ScheduledEvent, Position
from .._types import ID


__all__ = [
    "TrainStation",
    "Train",
    "ConnectingTrain",
    "IncompleteTrainMixin",
]


class TrainStation(Station):
    def __init__(
        self,
        station_id: ID,
        name: str,
        platform: ScheduledEvent[str] = None,
        arrival: ScheduledEvent[datetime] = None,
        departure: ScheduledEvent[datetime] = None,
        position: Position = None,
        distance: float = None,
        connections: Iterable[ConnectingTrain] = None,
    ):
        """
        Initialize a new :class:`TrainStation`

        :param station_id: The ID of the station
        :type station_id: Any
        :param name: The name of the station
        :type name: str
        :param platform: The platform that the vehicle is arriving at
        :type platform: ScheduledEvent[str]
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
        super().__init__(
            station_id=station_id,
            name=name,
            arrival=arrival,
            departure=departure,
            position=position,
            distance=distance,
            connections=connections,
        )
        self._platform = platform

    @property
    def platform(self) -> ScheduledEvent[str]:
        """
        The platform that the train is arriving at

        :return: The platform
        :rtype: ScheduledEvent[str]
        """
        return self._platform


class Train(PositionMixin, SpeedMixin, StationsMixin[TrainStation], Vehicle, metaclass=ABCMeta):
    """
    Interface specifying the attributes of a train
    """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id}>"

    def calculate_distance(self, station: Station) -> float:
        """
        Calculate the distance in meters between the train and a station

        :param station: The station to calculate the distance to
        :type station: Station
        :return: The distance in meters
        :rtype: float
        """
        return station.calculate_distance(self.distance or self.position)

    @property
    @abstractmethod
    def type(self) -> str:
        """
        The abbreviated train type

        :return: The train type
        :rtype: str
        """
        pass

    @property
    @abstractmethod
    def number(self) -> str:
        """
        The line number of this train

        :return: The line number
        :rtype: str
        """
        pass

    @property
    @abstractmethod
    def distance(self) -> float:
        """
        The distance from the start in meters

        :return: The distance
        :rtype: float
        """
        pass


@dataclass
class ConnectingTrain(ConnectingVehicle):
    """
    A connecting train is a train that is not part of the main trip but of a connecting service

    It may only have limited information available
    """

    platform: ScheduledEvent[str] | None
    """
    The platform where the train will depart from
    """


class IncompleteTrainMixin(IncompleteVehicleMixin, Train):
    """
    Class that implements all remaining abstract methods.
    Used when the operator does not provide the requested data via the API.
    """

    @property
    def id(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def type(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def number(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def stations_dict(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def origin(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def current_station(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def destination(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def distance(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def delay(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def position(self) -> NoReturn:
        raise NotImplementedInAPIError()

    @property
    def speed(self) -> NoReturn:
        raise NotImplementedInAPIError()
