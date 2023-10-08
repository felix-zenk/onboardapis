from abc import ABCMeta, abstractmethod

from .data import Position


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
