from typing import Protocol

from ._types import ID, StationType


class SupportsPosition(Protocol):
    @property
    def position(self) -> float: ...


class SupportsSpeed(Protocol):
    @property
    def speed(self) -> float: ...


class SupportsStations(Protocol):
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
