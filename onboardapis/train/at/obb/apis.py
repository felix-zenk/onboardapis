from __future__ import annotations

import logging

from ....units import meters_per_second
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
        return meters_per_second(
            kilometers_per_hour=self._api['gps']['JSON']['speed']
            if 'gps' in self._api
            else self._api['combined']['latestStatus']['speed']
        )

    @property
    def position(self) -> Position:
        return Position(
            latitude=self._api['gps']['JSON']['lat'],
            longitude=self._api['gps']['JSON']['lon'],
            # these are only present in newer trains
            altitude=self._api['gps']['JSON'].get('alt', None),
            heading=self._api['gps']['JSON'].get('bearing', None),
        ) if 'gps' in self._api else Position(
            latitude=self._api['combined']['latestStatus']['gpsPosition']['latitude'],
            longitude=self._api['combined']['latestStatus']['gpsPosition']['longitude'],
            altitude=None,
            heading=self._api['combined']['latestStatus']['gpsPosition']['orientation'],  # may be None, always provided
        )
