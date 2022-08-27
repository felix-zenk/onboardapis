"""
Implementation of the austrian operator ÖBB (Österreichische Bundesbahnen).
"""

import datetime
import time
from typing import Dict, Optional, Any, Tuple

from .. import Train, Station, ConnectingTrain
from ...exceptions import DataInvalidError
from ...utils.conversions import kmh_to_ms
from ...utils.data import StaticDataConnector, DynamicDataConnector, JSONDataConnector, some_or_default, ScheduledEvent

API_BASE_URL_RAILNET_REGIO = "railnet.oebb.at"


class _RailnetStaticConnector(StaticDataConnector, JSONDataConnector):
    def __init__(self):
        super().__init__(base_url=API_BASE_URL_RAILNET_REGIO)

    def refresh(self):
        self.store("trainInfo", self._get("/api/trainInfo"))


class _RailnetDynamicConnector(DynamicDataConnector, JSONDataConnector):
    def __init__(self):
        super().__init__(base_url=API_BASE_URL_RAILNET_REGIO)

    def refresh(self):
        self.store("combined", self._get("/assets/modules/fis/combined.json", params={"_time": time.time()}))


class RailnetRegio(Train):
    def __init__(self):
        super().__init__()
        self._static_data = _RailnetStaticConnector()
        self._dynamic_data = _RailnetDynamicConnector()

    def now(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            int(some_or_default(
                self._dynamic_data.load('combined', {}).get('operationalMessagesInfo', {}).get('time'), default=0
            ))
        )

    @property
    def type(self) -> str:
        return self._static_data.load('trainInfo', {}).get('trainType', None)

    @property
    def number(self) -> str:
        return self._static_data.load('trainInfo', {}).get('lineNumber', None)

    @property
    def id(self) -> None:
        # Not available in Railnet
        return None

    @property
    def stations(self) -> Dict[Any, Station]:
        def to_datetime(data: str, __future: bool = None) -> Optional[datetime.datetime]:
            if some_or_default(data, default=None) is None:
                return None
            # Now
            now = self.now()
            # Assume that the day is the same as the current day
            obj = datetime.datetime.strptime(data, "%H:%M").replace(year=now.year, month=now.month, day=now.day)

            if __future is not None:
                # We know that the event is in the future,
                # but obj is currently in the past
                if __future and obj < now:
                    obj += datetime.timedelta(days=1)
                # We know that the event is in the past,
                # but obj is currently in the future
                elif not __future and obj > now:
                    obj -= datetime.timedelta(days=1)
            return obj

        stations = {}
        distance = 0.0
        future = False
        for station_json in self._dynamic_data.load('combined', {}).get('stationList', []):
            # The first station has no distance
            if station_json.get('distance', "") != "":
                distance += float(some_or_default(station_json.get('distance'), default=0.0))

            connections = list([
                ConnectingTrain(
                    train_type=connection.get('type', None),
                    line_number=connection.get('line', None),
                    platform=ScheduledEvent(
                        scheduled=connection.get('track', {}).get('all', None),
                        actual=connection.get('track', {}).get('all', None)
                    ),
                    destination=connection.get('destination', {}).get('all', None),
                    departure=ScheduledEvent(
                        scheduled=to_datetime(connection.get('schedule', None), True),
                        actual=to_datetime(connection.get('actual', None), True)
                    )
                )
                for connection in self._dynamic_data.load('combined').get('connectionInfo', {}).get('connections', [])
                if self._dynamic_data.load('combined').get('connectionInfo', {}).get('station_id', -1)
                == station_json.get('id', -2)
            ])

            stations[station_json.get('id')] = Station(
                station_id=station_json.get('id'),
                name=station_json.get('name', {}).get('all', None),
                platform=ScheduledEvent(
                    station_json.get('track', {}).get('all', None),
                    station_json.get('track', {}).get('all', None)
                ),
                arrival=ScheduledEvent(
                    to_datetime(station_json.get('arrivalSchedule', None), self.delay > 0 if future else False),
                    to_datetime(station_json.get('arrivalForecast', None), future)
                ),
                departure=ScheduledEvent(
                    to_datetime(station_json.get('departureSchedule', None), self.delay > 0 if future else False),
                    to_datetime(station_json.get('departureForecast', None), future)
                ),
                distance=distance,
                connections=connections
            )

            future = future or station_json.get('id', -1) == self._dynamic_data.load('combined', {}).get(
                'currentStation', {}).get('id', None)
        return stations

    @property
    def origin(self) -> Station:
        return super(RailnetRegio, self).origin

    @property
    def current_station(self) -> Station:
        # Get the current station id
        station_id = self._dynamic_data.load('combined', {}).get('currentStation', {}).get('id', -1)
        # Get the station from the stations dict
        try:
            return self.stations[station_id]
        except AttributeError as e:
            raise DataInvalidError("No current station found") from e

    @property
    def destination(self) -> Station:
        return super(RailnetRegio, self).destination

    @property
    def speed(self) -> float:
        return kmh_to_ms(
            float(self._dynamic_data.load('combined', {}).get('operationalMessagesInfo', {}).get('speed', 0)))

    @property
    def distance(self) -> float:
        try:
            return self.stations[self._dynamic_data.load(
                'combined', {}).get('operationalMessagesInfo', {}).get('distanceStation', -1)
                   ].distance + float(
                self._dynamic_data.load('combined', {}).get('operationalMessagesInfo', {}).get('distance', 0)
            )
        except AttributeError as e:
            raise DataInvalidError("No base station found for distance") from e

    @property
    def position(self) -> Tuple[float, float]:
        map_info = self._dynamic_data.load('combined', {}).get('mapInfo', {})
        return (
            float(map_info.get('latitude')) if some_or_default(map_info.get('latitude')) is not None else None,
            float(map_info.get('longitude')) if some_or_default(map_info.get('longitude')) is not None else None
        )

    @property
    def delay(self) -> float:
        return float(self._dynamic_data.load('combined', {}).get('operationalMessagesInfo', {}).get('delay', 0))
