from __future__ import annotations

import logging

from ....units import ms
from ....data import Position
from ... import Train
from .interfaces import RailnetRegioAPI

logger = logging.getLogger(__name__)


class RailnetRegio(Train):
    """
    Wrapper for interacting with the ÖBB RailnetRegio API
    """

    _api: RailnetRegioAPI

    def __init__(self):
        self._data = RailnetRegioAPI()
        Train.__init__(self)

    @property
    def speed(self) -> float:
        return ms(kmh=self._data['gps']['JSON']['speed'])

    @property
    def position(self) -> Position:
        return Position(
            latitude=self._data['gps']['JSON']['lat'],
            longitude=self._data['gps']['JSON']['lon'],
            # these are only present in newer trains
            altitude=self._data['gps']['JSON'].get('alt', None),
            heading=self._data['gps']['JSON'].get('bearing', None),
        )
