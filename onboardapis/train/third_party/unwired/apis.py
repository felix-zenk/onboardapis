from __future__ import annotations

import logging
import re

from abc import ABCMeta
from datetime import datetime, timedelta

from ....mixins import StationsMixin, InternetAccessMixin, SpeedMixin, PositionMixin
from ....data import Position, ScheduledEvent, ID
from ... import Train, TrainStation
from .interfaces import GenericUnwiredAPI

logger = logging.getLogger(__name__)


class GenericUnwiredTrain(Train, InternetAccessMixin):
    _api = GenericUnwiredAPI

    def __init__(self):
        self._data = GenericUnwiredAPI()
        Train.__init__(self)
        InternetAccessMixin.__init__(self)

    @property
    def id(self) -> ID:
        return self._data['journey']['id']

    @property
    def type(self) -> str:
        return re.match(r'(\w+)\d+', self._data['journey']['line']).group(1)

    @property
    def line_number(self) -> str:
        return re.match(r'\w+(\d+)', self._data['journey']['line']).group(1)


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
            lambda s: self.now() < s.arrival.actual,
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
