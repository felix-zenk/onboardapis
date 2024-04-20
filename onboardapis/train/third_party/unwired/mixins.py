from __future__ import annotations

import logging
from abc import ABCMeta
from datetime import datetime, timedelta

from ....mixins import SpeedMixin, PositionMixin, StationsMixin
from ....data import Position, ScheduledEvent, ID
from ... import Train, TrainStation

logger = logging.getLogger(__name__)

__all__ = [
    "UnwiredJourneyMixin",
    "UnwiredMapMixin",
]


class UnwiredJourneyMixin(Train, StationsMixin[TrainStation], metaclass=ABCMeta):
    @property
    def stations_dict(self) -> dict[ID, TrainStation]:
        return {
            station['id']: TrainStation(
                id=station['id'],
                name=station['name'],
                arrival=ScheduledEvent(
                    scheduled=(
                        datetime.fromisoformat(station['arrivalPlanned']).replace(tzinfo=None)
                        if 'arrivalPlanned' in station.keys() else None
                    ),
                    actual=(
                        datetime.fromisoformat(station['arrivalPlanned']).replace(tzinfo=None)
                        + timedelta(minutes=station['arrivalDelay'])
                        if 'arrivalDelay' in station.keys() else None
                    )
                ),
                departure=ScheduledEvent(
                    scheduled=(
                        datetime.fromisoformat(station['departurePlanned']).replace(tzinfo=None)
                        if 'departurePlanned' in station.keys() else None
                    ),
                    actual=(
                        datetime.fromisoformat(station['departurePlanned']).replace(tzinfo=None)
                        + timedelta(minutes=station['departureDelay'])
                        if 'departureDelay' in station.keys() else None
                    ),
                ),
                distance=None,
                position=None,
                platform=None,
                _connections=(),
            )
            for station in self._api['journey']['stops']
        }

    @property
    def current_station(self) -> TrainStation:
        station, *_ = filter(
            lambda s: self.now < s.arrival.actual,
            filter(
                lambda s: s.arrival.actual is not None,
                self.stations
            )
        )
        return station


class UnwiredMapMixin(SpeedMixin, PositionMixin, metaclass=ABCMeta):
    @property
    def position(self) -> Position:
        raise NotImplementedError
