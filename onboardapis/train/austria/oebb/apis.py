from __future__ import annotations

import datetime

from ...._types import ID
from ....exceptions import DataInvalidError
from ....conversions import kmh_to_ms
from ....data import (
    default,
    ScheduledEvent,
    Position,
)
from ... import Train, ConnectingTrain, TrainStation
from .connectors import RailnetConnector


class RailnetRegio(Train):
    """
    Wrapper for interacting with the ÖBB RailnetRegio API
    """

    _data = RailnetConnector()

    def now(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            int(
                default(
                    self._data["combined"].get("operationalMessagesInfo", {}).get("time"),
                    __default=0,
                )
            )
        )

    @property
    def type(self) -> str:
        return self._data["train_info"].get("trainType", None)

    @property
    def number(self) -> str:
        return self._data["train_info"].get("lineNumber", None)

    @property
    def id(self) -> None:
        # Not available in Railnet
        return None  # TODO IncompleteTrainMixin?

    @property
    def stations_dict(self) -> dict[ID, TrainStation]:
        def to_datetime(data: str, __future: bool = None) -> datetime.datetime | None:
            if default(data, __default=None) is None:
                return None
            # Now
            now = self.now()
            # Assume that the day is the same as the current day
            obj = datetime.datetime.strptime(data, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )

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
        for station_json in self._data["combined"].get(
            "stationList", []
        ):
            # The first station has no distance
            if station_json.get("distance", "") != "":
                distance += float(
                    default(station_json.get("distance"), __default=0.0)
                )

            connections = list(
                [
                    ConnectingTrain(
                        vehicle_type=connection.get("type", None),
                        line_number=connection.get("line", None),
                        platform=ScheduledEvent(
                            scheduled=connection.get("track", {}).get("all", None),
                            actual=connection.get("track", {}).get("all", None),
                        ),
                        destination=connection.get("destination", {}).get("all", None),
                        departure=ScheduledEvent(
                            scheduled=to_datetime(
                                connection.get("schedule", None), True
                            ),
                            actual=to_datetime(connection.get("actual", None), True),
                        ),
                    )
                    for connection in self._data["combined"].get("connectionInfo", {}).get("connections", [])
                    if self._data["combined"].get("connectionInfo", {}).get("station_id", -1) == station_json.get("id")
                ]
            )

            stations[station_json.get("id")] = TrainStation(
                station_id=station_json.get("id"),
                name=station_json.get("name", {}).get("all", None),
                platform=ScheduledEvent(
                    station_json.get("track", {}).get("all", None),
                    station_json.get("track", {}).get("all", None),
                ),
                arrival=ScheduledEvent(
                    to_datetime(
                        station_json.get("arrivalSchedule", None),
                        self.delay > 0 if future else False,
                    ),
                    to_datetime(station_json.get("arrivalForecast", None), future),
                ),
                departure=ScheduledEvent(
                    to_datetime(
                        station_json.get("departureSchedule", None),
                        self.delay > 0 if future else False,
                    ),
                    to_datetime(station_json.get("departureForecast", None), future),
                ),
                distance=distance,
                connections=connections,
            )

            future = future or station_json.get("id", -1) == self._data["combined"].get("currentStation", {}).get("id")
        return stations

    @property
    def current_station(self) -> TrainStation:
        # Get the current station id
        station_id = (
            self._data["combined"]
            .get("currentStation", {})
            .get("id", -1)
        )
        # Get the station from the stations dict
        try:
            return self.stations_dict[station_id]
        except AttributeError as e:
            raise DataInvalidError("No current station found") from e

    @property
    def speed(self) -> float:
        return kmh_to_ms(
            float(
                self._data["combined"]
                .get("operationalMessagesInfo", {})
                .get("speed", 0)
            )
        )

    @property
    def distance(self) -> float:
        try:
            return self.stations_dict[
                self._data["combined"]
                .get("operationalMessagesInfo", {})
                .get("distanceStation", -1)
            ].distance + float(
                self._data["combined"]
                .get("operationalMessagesInfo", {})
                .get("distance", 0)
            )
        except AttributeError as e:
            raise DataInvalidError("No base station found for distance") from e

    @property
    def position(self) -> Position:
        map_info = self._data["combined"].get("mapInfo", {})
        return Position(
            latitude=(
                float(map_info.get("latitude"))
                if default(map_info.get("latitude")) is not None
                else None
            ),
            longitude=(
                float(map_info.get("longitude"))
                if default(map_info.get("longitude")) is not None
                else None
            ),
        )

    @property
    def delay(self) -> float:
        return float(
            self._data["combined"]
            .get("operationalMessagesInfo", {})
            .get("delay", 0)
        )
