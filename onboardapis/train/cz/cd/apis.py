from __future__ import annotations

import logging

from .interfaces import OnBoardPortalAPI
from .schema import CdObpRealtimeSchema
from ....data import Position
from ....mixins import PositionMixin, SpeedMixin
from ....train import Train
from ....units import meters_per_second

logger = logging.getLogger(__name__)


class OnBoardPortal(Train, PositionMixin, SpeedMixin):
    _api: OnBoardPortalAPI
    # _internet_access: OnBoardAPIInternetInterface # Data usage limit was removed, no necessity to implement rn

    def __init__(self) -> None:
        self._api = OnBoardPortalAPI()
        # self._internet_access = NotImplemented
        Train.__init__(self)

    @property
    def type(self) -> str | None:
        return (self._api['info'] or {}).get('group')

    @property
    def line_number(self) -> str | None:
        return (self._api['current'] or {}).get('line')

    @property
    def position(self) -> Position | None:
        if self._api['realtime'] is None:
            return None
        realtime: CdObpRealtimeSchema = self._api['realtime']
        return Position(latitude=realtime['gpsLat'], longitude=realtime['gpsLng'], altitude=realtime['altitude'])

    @property
    def speed(self) -> float | None:
        if self._api['realtime'] is None:
            return None
        realtime: CdObpRealtimeSchema = self._api['realtime']
        return meters_per_second(kilometers_per_hour=realtime['speed'])

    @property
    def temperature(self) -> float | None:
        return (self._api['realtime'] or {}).get('temperature')

    @property
    def delay(self) -> int | None:
        return (self._api['realtime'] or {}).get('delay')
