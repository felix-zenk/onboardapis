"""
Module for defining protocols for type checking.

The protocols defined here match the properties of the classes in `onboardapis.mixins`.
"""
from __future__ import annotations

from typing import Protocol

from .data import ID, StationType, Position
from .mixins import InternetAccessInterface


class SupportsPosition(Protocol):
    # noinspection PyPropertyDefinition
    @property
    def position(self) -> Position: ...


class SupportsSpeed(Protocol):
    # noinspection PyPropertyDefinition
    @property
    def speed(self) -> float: ...


class SupportsStations(Protocol):
    def calculate_distance(self, station: StationType): ...

    # noinspection PyPropertyDefinition
    @property
    def stations_dict(self) -> dict[ID, StationType]: ...

    # noinspection PyPropertyDefinition
    @property
    def stations(self) -> list[StationType]: ...

    # noinspection PyPropertyDefinition
    @property
    def origin(self) -> StationType: ...

    # noinspection PyPropertyDefinition
    @property
    def current_station(self) -> StationType: ...

    # noinspection PyPropertyDefinition
    @property
    def destination(self) -> StationType: ...

    # noinspection PyPropertyDefinition
    @property
    def delay(self) -> float: ...

    # noinspection PyPropertyDefinition
    @property
    def distance(self) -> float: ...


class SupportsInternetAccess(Protocol):
    # noinspection PyPropertyDefinition
    @property
    def internet_access(self) -> InternetAccessInterface: ...
