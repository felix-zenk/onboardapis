"""
Module for defining protocols for type checking.

The protocols defined here match the properties of the classes in `onboardapis.mixins`.
"""
from __future__ import annotations

from typing import Protocol

from .data import ID, StationType, Position, InternetAccessInterface


class SupportsPosition(Protocol):
    @property
    def position(self) -> Position: ...


class SupportsSpeed(Protocol):
    @property
    def speed(self) -> float: ...


class SupportsStations(Protocol):
    def calculate_distance(self, station: StationType): ...

    @property
    def stations_dict(self) -> dict[ID, StationType]: ...

    @property
    def stations(self) -> list[StationType]: ...

    @property
    def origin(self) -> StationType: ...

    @property
    def current_station(self) -> StationType: ...

    @property
    def destination(self) -> StationType: ...

    @property
    def delay(self) -> float: ...

    @property
    def distance(self) -> float: ...


class SupportsInternetAccess(Protocol):
    @property
    def internet_access(self) -> InternetAccessInterface: ...
