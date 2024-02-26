"""
Package for trains

## Operator ID

The operator ID for trains is different depending on the region.

For Europe, the operator ID is the [VKM register code](https://www.era.europa.eu/domains/registers/vkm_en).
"""
from __future__ import annotations

from abc import ABCMeta, abstractmethod

from .. import Vehicle, Station, ConnectingVehicle
from ..data import ScheduledEvent


__all__ = [
    'TrainStation',
    'Train',
    'ConnectingTrain',
]


class TrainStation(Station):
    """
    An `onboardapis.Station` with the additional information of a platform
    """
    platform: ScheduledEvent[str] | None


class Train(Vehicle, metaclass=ABCMeta):
    """
    Base class for all train implementations.
    """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id}>"

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


class ConnectingTrain(ConnectingVehicle):
    """
    A connecting train is a train that is not part of the main trip but of a connecting service

    It may only have limited information available
    """

    platform: ScheduledEvent[str] | None
    """
    The platform where the train will depart from
    """
