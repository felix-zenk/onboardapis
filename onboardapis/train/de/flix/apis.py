from __future__ import annotations

import logging

from ....units import ms
from ....data import Position
from ....mixins import PositionMixin, SpeedMixin
from ... import Train
from .interfaces import FlixTainmentAPI

logger = logging.getLogger(__name__)


class FlixTainment(Train, SpeedMixin, PositionMixin):
    """Wrapper for interacting with the Flixtrain FLIXTainment API
    (few methods are available, because the API is very sparse)."""

    _api: FlixTainmentAPI

    def __init__(self):
        self._api = FlixTainmentAPI()
        Train.__init__(self)

    @property
    def position(self) -> Position:
        return Position(
            latitude=self._api["position"].get("latitude", None),
            longitude=self._api["position"].get("longitude", None),
        )

    @property
    def speed(self) -> float:
        return ms(kmh=float(self._api["position"].get("speed", 0.0)))

    @property
    def type(self) -> str:
        return 'FLX'
