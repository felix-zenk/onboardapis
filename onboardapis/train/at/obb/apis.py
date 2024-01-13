from __future__ import annotations

from ....units import ms
from ....data import Position
from ... import Train, IncompleteTrainMixin
from .connectors import RailnetRegioConnector


class RailnetRegio(IncompleteTrainMixin, Train):
    """
    Wrapper for interacting with the ÖBB RailnetRegio API
    """

    _data: RailnetRegioConnector

    def __init__(self):
        self._data = RailnetRegioConnector()
        super().__init__()

    @property
    def speed(self) -> float:
        return ms(kmh=self._data['gps']['JSON']['speed'])

    @property
    def position(self) -> Position:
        return Position(
            latitude=self._data['gps']['JSON']['lat'],
            longitude=self._data['gps']['JSON']['lon'],
        )
