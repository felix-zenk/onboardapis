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
        self._api = RailnetRegioAPI()
        Train.__init__(self)

    @property
    def speed(self) -> float:
        return ms(kmh=self._api['gps']['JSON']['speed'])

    @property
    def position(self) -> Position:
        return Position(
            latitude=self._api['gps']['JSON']['lat'],
            longitude=self._api['gps']['JSON']['lon'],
            # these are only present in newer trains
            altitude=self._api['gps']['JSON'].get('alt', None),
            heading=self._api['gps']['JSON'].get('bearing', None),
        )
