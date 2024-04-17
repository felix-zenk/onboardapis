from __future__ import annotations

import logging

from datetime import datetime, timedelta

from ....data import ID
from ....exceptions import DataInvalidError
from ....units import ms
from ... import Train, TrainStation
from .interfaces import PortaleRegionaleConnector

logger = logging.getLogger(__name__)


class PortaleRegionale(Train):
    """
    Wrapper for interacting with the Trenitalia PortaleRegionale API
    """

    _api: PortaleRegionaleConnector

    _stations: dict[ID, TrainStation]
    """A dict that contains the known stations (origin, destination and passed stations)"""

    def __init__(self):
        self._data = PortaleRegionaleConnector()
        self._stations = dict()
        Train.__init__(self)

    def now(self) -> datetime:
        return datetime.fromisoformat(self._data['infovaggio']['datetime'])

    @property
    def id(self) -> ID:
        return self.line_number

    @property
    def line_number(self) -> str:
        return self._data['infovaggio']['infos']['trackNumber']

    def delay(self) -> timedelta:
        delay_minutes = self._data['infovaggio']['infos'].get('delay', '')
        return timedelta() if delay_minutes in ('0', '') else timedelta(minutes=int(delay_minutes))

    @property
    def speed(self) -> float:
        if self._data['infovaggio'].get('isGpsValid', 'false').lower() == 'true':
            return ms(kmh=(float(self._data['infovaggio']['infos']['speed'])))
        raise DataInvalidError('GPS data invalid.')

    @property
    def stations_dict(self) -> dict[ID, TrainStation]:
        first = self._data['infovaggio']['infos']['stazionePartenza']
        current = self._data['infovaggio']['nextStation']
        last = self._data['infovaggio']['infos']['stazioneArrivo']

        if len(self._stations) == 0:
            self._stations = {
                first: TrainStation(
                    id=first, name=first,
                    arrival=None, departure=None, position=None, distance=None, _connections=(), platform=None
                ),
                current: TrainStation(
                    id=current, name=current,
                    arrival=None, departure=None, position=None, distance=None, _connections=(), platform=None
                ),  # if current == first Python will just overwrite the entry
                last: TrainStation(
                    id=last, name=last,
                    arrival=None, departure=None, position=None, distance=None, _connections=(), platform=None
                ),
            }
            return self._stations.copy()

        self._stations = {
            first: TrainStation(
                id=first, name=first,
                arrival=None, departure=None, position=None, distance=None, _connections=(), platform=None
            ),
            **{key: value for key, value in tuple(self._stations.items())[1:-1]},
            current: TrainStation(
                id=current, name=current,
                arrival=None, departure=None, position=None, distance=None, _connections=(), platform=None
            ),
            last: TrainStation(
                id=last, name=last,
                arrival=None, departure=None, position=None, distance=None, _connections=(), platform=None
            ),  # if current == last Python will just overwrite the entry
        }
        return self._stations.copy()

    @property
    def current_station(self) -> TrainStation:
        return self.stations_dict[self._data['infovaggio']['nextStation']]
