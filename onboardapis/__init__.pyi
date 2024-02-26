from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Self, Iterable

from ._types import ID
from .data import DataConnector, ScheduledEvent, Position


class API(object): ...

class Vehicle(API, metaclass=ABCMeta):
    _data: DataConnector

    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...

    def init(self) -> None: ...
    def shutdown(self) -> None: ...
    def now(self) -> datetime: ...
    @property
    @abstractmethod
    def id(self) -> ID: ...

@dataclass
class ConnectingVehicle(object):
    vehicle_type: str | None
    line_number: str | None
    departure: ScheduledEvent[datetime] | None
    destination: str | None

@dataclass
class Station(object):
    id: ID
    name: str
    arrival: ScheduledEvent[datetime] | None
    departure: ScheduledEvent[datetime] | None
    position: Position | None
    distance: float | None
    _connections: Iterable[ConnectingVehicle]

    @property
    def connections(self) -> list[ConnectingVehicle]: ...
    def calculate_distance(self, other: Station | Position | int | float) -> float | None: ...
