from datetime import datetime, timedelta

from ...._types import ID
from ....units import meters, seconds
from ... import Train, IncompleteTrainMixin, TrainStation
from .connectors import PortaleRegionaleConnector


class PortaleRegionale(IncompleteTrainMixin, Train):
    """
    Wrapper for interacting with the Trenitalia PortaleRegionale API
    """

    _data = PortaleRegionaleConnector()

    _stations: dict[ID, TrainStation]
    """A dict that contains the known stations (origin, destination and passed stations)"""

    def __init__(self):
        IncompleteTrainMixin.__init__(self)
        Train.__init__(self)
        self._stations = dict()

    def now(self) -> datetime:
        return datetime.fromisoformat(self._data['infovaggio']['datetime'])

    @property
    def number(self) -> str:
        return self._data['infovaggio']['infos']['trackNumber']

    def delay(self) -> timedelta:
        delay_minutes = self._data['infovaggio']['infos'].get('delay', '')
        return timedelta() if delay_minutes in ('0', '') else timedelta(minutes=int(delay_minutes))

    @property
    def speed(self) -> float:
        if self._data['infovaggio'].get('isGpsValid', 'false') == 'true':
            return meters(kilometers=seconds(hours=(float(self._data['infovaggio']['infos']['speed']))))
        return 0.

    @property
    def stations_dict(self) -> dict[ID, TrainStation]:
        first = self._data['infovaggio']['infos']['stazionePartenza']
        current = self._data['infovaggio']['nextStation']
        last = self._data['infovaggio']['infos']['stazioneArrivo']

        if len(self._stations) == 0:
            self._stations = {
                first: TrainStation(station_id=first, name=first),
                current: TrainStation(station_id=current, name=current),
                last: TrainStation(station_id=last, name=last),
            }
        else:
            self._stations = {
                first: TrainStation(station_id=first, name=first),
                **{key: value for key, value in tuple(self._stations.items())[1:-1]},
                current: TrainStation(station_id=current, name=current),
                last: TrainStation(station_id=last, name=last),
            }

        return self._stations.copy()

    @property
    def current_station(self) -> TrainStation:
        return self.stations_dict[self._data['infovaggio']['nextStation']]

    @property
    def id(self) -> ID:
        return self.number
