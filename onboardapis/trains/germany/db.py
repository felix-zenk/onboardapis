"""
Implementation of the german operator DB (Deutsche Bahn).
"""

import datetime

from typing import Tuple, Dict, Any, List, Optional, Literal

from .. import Train, Station, ConnectingTrain, _LazyStation
from ...exceptions import DataInvalidError
from ...utils.conversions import kmh_to_ms
from ...utils.data import DynamicDataConnector, JSONDataConnector, StaticDataConnector, some_or_default, ScheduledEvent

API_BASE_URL_ICEPORTAL = "iceportal.de"
InternetStatus = Literal["NO_INFO", "NO_INTERNET", "UNSTABLE", "WEAK", "MIDDLE", "HIGH"]


class _ICEPortalStaticConnector(StaticDataConnector, JSONDataConnector):
    __slots__ = []

    def __init__(self):
        super().__init__(base_url=API_BASE_URL_ICEPORTAL)

    def refresh(self):
        self.store("bap", self._get("/bap/api/bap-service-status"))


class _ICEPortalDynamicConnector(DynamicDataConnector, JSONDataConnector):
    __slots__ = ["_connections"]

    def __init__(self):
        super().__init__(base_url=API_BASE_URL_ICEPORTAL)
        self._connections = {}
        """
        A cache for connections
        Connections for DB are only available shortly before the arrival
        -> Cache every already seen connection as well
        """

    def refresh(self):
        self.store("status", self._get("/api1/rs/status"))
        self.store("trip", self._get("/api1/rs/tripInfo/trip"))

    def connections(self, station_id: str) -> List[ConnectingTrain]:
        """
        Get all connections for a station

        :param station_id: The station to get the connections for
        :type station_id: str
        :return: A list of connections for the station
        :rtype: List[ConnectingTrain]
        """
        if self._connections.get(station_id) is not None:
            return self._connections.get(station_id)
        connections = [
            ConnectingTrain(
                train_type=data.get('trainType', None),
                line_number=data.get('vzn', None),
                platform=ScheduledEvent(
                    scheduled=data.get('track', {}).get('scheduled', None),
                    actual=data.get('track', {}).get('actual', None),
                ),
                destination=data.get('station', {}).get('name', None),
                departure=ScheduledEvent(
                    scheduled=datetime.datetime.fromtimestamp(
                        some_or_default(data.get('timetable', {}).get('scheduledDepartureTime', None), default=0)
                    ),
                    actual=datetime.datetime.fromtimestamp(
                        some_or_default(data.get('timetable', {}).get('actualDepartureTime', None), default=0)
                    ),
                )
            )
            for data in self._get(f"/api1/rs/tripInfo/trip/{station_id}").get(station_id, {}).get('connections', [])
        ]
        self._connections[station_id] = connections
        return connections


class ICEPortal(Train):
    """
    Wrapper for interacting with the DB ICE Portal API
    """
    __slots__ = []

    def __init__(self):
        super().__init__()
        self._static_data = _ICEPortalStaticConnector()
        self._dynamic_data = _ICEPortalDynamicConnector()

    def now(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            int(some_or_default(self._dynamic_data.load("status", {}).get('serverTime', None), default=0)) / 1000
        )

    @property
    def id(self) -> str:
        return self._dynamic_data.load("status", {}).get('tzn')

    @property
    def type(self) -> str:
        return self._dynamic_data.load("trip", {}).get('trip', {}).get('trainType')

    @property
    def number(self) -> str:
        return self._dynamic_data.load("trip", {}).get('trip', {}).get('vzn')

    @property
    def stations(self) -> Dict[str, Station]:
        # Each stations connecting trains require an additional request
        # So use a LazyStation to only request the connections when needed
        return {
            stop.get('station', {}).get('evaNr'): _LazyStation(
                station_id=stop.get('station', {}).get('evaNr'),
                name=stop.get('station', {}).get('name'),
                platform=ScheduledEvent(
                    scheduled=stop.get('track', {}).get('scheduled'),
                    actual=stop.get('track', {}).get('actual')
                ),
                arrival=ScheduledEvent(
                    scheduled=datetime.datetime.fromtimestamp(
                        int(some_or_default(stop.get('timetable', {}).get('scheduledArrivalTime'), default=0)) / 1000
                    ) if some_or_default(stop.get('timetable', {}).get('scheduledArrivalTime')) is not None else None,
                    actual=datetime.datetime.fromtimestamp(
                        (some_or_default(stop.get('timetable', {}).get('actualArrivalTime'), default=0)) / 1000
                    ) if some_or_default(stop.get('timetable', {}).get('actualArrivalTime')) is not None else None,
                ),
                departure=ScheduledEvent(
                    scheduled=datetime.datetime.fromtimestamp(
                        int(some_or_default(stop.get('timetable', {}).get('scheduledDepartureTime'), default=0)) / 1000
                    ) if some_or_default(stop.get('timetable', {}).get('scheduledDepartureTime')) is not None else None,
                    actual=datetime.datetime.fromtimestamp(
                        int(some_or_default(stop.get('timetable', {}).get('actualDepartureTime'), default=0)) / 1000
                    ) if some_or_default(stop.get('timetable', {}).get('actualDepartureTime')) is not None else None,
                ),
                position=(
                    stop.get('station', {}).get('geocoordinates', {}).get('latitude'),
                    stop.get('station', {}).get('geocoordinates', {}).get('longitude')
                ),
                distance=stop.get('info', {}).get('distanceFromStart', 0),
                connections=None,
                lazy_func=lambda: self._dynamic_data.connections(stop.get('station', {}).get('evaNr')),
            )
            for stop in self._dynamic_data.load("trip", {}).get('trip', {}).get('stops', [])
        }

    @property
    def origin(self) -> Station:
        return super(ICEPortal, self).origin

    @property
    def current_station(self) -> Station:
        # Get the current station id
        stop_info = self._dynamic_data.load("trip", {}).get('trip', {}).get('stopInfo', {})
        station_id = some_or_default(stop_info.get('actualNext'))
        # Get the station from the stations dict
        try:
            return self.stations[station_id]
        except AttributeError as e:
            raise DataInvalidError("No current station found") from e

    @property
    def destination(self) -> Station:
        return super(ICEPortal, self).destination

    @property
    def speed(self) -> float:
        return kmh_to_ms(self._dynamic_data.load("status", {}).get('speed', 0))

    @property
    def distance(self) -> float:
        return self._dynamic_data.load("trip", {}).get('trip', {}).get('actualPosition', 0)

    @property
    def position(self) -> Tuple[float, float]:
        return (
            self._dynamic_data.load("status", {}).get('latitude'),
            self._dynamic_data.load("status", {}).get('longitude')
        )

    @property
    def delay(self) -> float:
        return super(ICEPortal, self).delay

    def all_delay_reasons(self) -> Dict[str, Optional[List[str]]]:
        """
        Get all delay reasons for the current trip

        :return: A dictionary of delay reasons
        :rtype: Dict[str, Optional[List[str]]]
        """
        return {
            stop.get('station', {}).get('evaNr', None): list([
                some_or_default(reason.get('text', None)) for reason in stop.get('delayReasons', [])
            ])
            for stop in self._dynamic_data.load("trip", {}).get('trip', {}).get('stops', [])
        }

    def delay_reasons(self) -> Optional[List[str]]:
        """
        Get the delay reason for the current station

        :return: The delay reason
        :rtype: Optional[List[str]]
        """
        return self.all_delay_reasons().get(self.current_station.id, None)

    def has_bap(self) -> bool:
        """
        Returns True if the train has a BAP module installed and active

        bap = 'Bestellen am Platz' is a service that allows passengers to order food and drinks right to their seat

        :return:
        """
        # bap is a service exclusive to first class
        if self.wagon_class() != "FIRST":
            return False
        # Check if the module is installed
        if str(self._dynamic_data.load("status", {}).get('bapInstalled', False)).lower() != "true":
            return False
        # Check if the module is active
        if str(self._static_data.load("bap", {}).get('status', False)).lower() == "true":
            return True
        return False

    def wagon_class(self) -> Optional[Literal["FIRST", "SECOND"]]:
        """
        Get the wagon class of the wagon you are currently in

        :return: The wagon class
        :rtype: Literal["FIRST", "SECOND"]
        """
        return some_or_default(self._dynamic_data.load("status", {}).get('wagonClass'))

    def internet_connection(self) -> Tuple[
        Optional[InternetStatus], Optional[InternetStatus], Optional[datetime.timedelta]
    ]:
        """
        Returns the internet connection status of the train,

        the next internet connection status,

        and the time until the change occurs

        :return: The tuple (current, next, time_remaining)
        :rtype: Tuple[InternetStatus, InternetStatus, datetime.timedelta]
        """
        return (
            # Current state
            some_or_default(self._dynamic_data.load("status", {}).get('connectivity', {}).get('currentState')),
            # Next state
            some_or_default(self._dynamic_data.load("status", {}).get('connectivity', {}).get('nextState')),
            # Remaining time
            datetime.timedelta(
                seconds=int(self._dynamic_data.load("status", {}).get('connectivity', {}).get('remainingTimeSeconds'))
            )
            if some_or_default(
                self._dynamic_data.load("status", {}).get('connectivity', {}).get('remainingTimeSeconds', '')
            ) is not None else None
        )
