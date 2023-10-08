"""
Implementation for the german operator DB (Deutsche Bahn).
"""
from __future__ import annotations

import datetime
import re

from typing import Tuple, Dict, List, Optional, Literal, Generator

from .. import Train, TrainStation, ConnectingTrain
from ...mixins import StationsMixin
from ...exceptions import DataInvalidError, APIConnectionError
from ...conversions import kmh_to_ms
from ...data import (
    DynamicDataConnector,
    JSONDataConnector,
    StaticDataConnector,
    some_or_default,
    ScheduledEvent,
    Position,
)

InternetStatus = Literal[
    "NO_INFO", "NO_INTERNET", "UNSTABLE", "WEAK", "MIDDLE", "HIGH"
]  # from /api1/rs/configs


class _ICEPortalStaticConnector(JSONDataConnector, StaticDataConnector):
    __slots__ = []

    API_URL = "iceportal.de"

    def refresh(self):
        # Bestellen am Platz
        self.store("bap", self._get("/bap/api/bap-service-status"))
        # train names (optional)
        try:
            self.store(
                "names",
                self._get(
                    "/projects/onboardapis/res/train/germany/db/names.json",
                    base_url="felix-zenk.github.io",
                ),
            )
        # Try to get the names from GitHub. If there is no internet connection, then don't use names.
        except ConnectionError:
            self.store("names", {})


class _ICEPortalDynamicConnector(JSONDataConnector, DynamicDataConnector):
    __slots__ = ["_connections_cache_control"]

    API_URL = "iceportal.de"

    def __init__(self):
        super().__init__()
        self._connections_cache_control = {}
        """
        A cache for connections
        Connections for DB are only available shortly before the arrival
        -> Cache every already seen connection as well
        """

    def refresh(self):
        # status
        self.store("status", self._get("/api1/rs/status"))
        # trip
        self.store("trip", self._get("/api1/rs/tripInfo/trip"))

    def connections(self, station_id: str) -> Generator[ConnectingTrain, None, None]:
        """
        Get all connections for a station

        :param station_id: The station to get the connections for
        :type station_id: str
        :return: A generator yielding a list of connections for the station
        :rtype: Generator[list[ConnectingTrain]]
        """

        # Function to determine when to update the cache
        def cache_valid() -> bool:
            last_update = self._connections_cache_control.get(station_id, {}).get(
                "last_update"
            )
            if last_update is None:
                return False
            return datetime.datetime.now() < last_update + datetime.timedelta(minutes=1)

        # Let the cache expire after 1 minute
        if cache_valid():
            yield from self.load(f"connections_{station_id}", [])
            return

        # Request the connections
        try:
            connections_json = self._get(f"/api1/rs/tripInfo/connection/{station_id}")
        except APIConnectionError:
            # Try to return the last cached connections if new connections could not be fetched
            yield from self.load(f"connections_{station_id}", [])
            return

        # Process the connections
        connections = list(
            [
                ConnectingTrain(
                    vehicle_type=connection.get("trainType", None),
                    line_number=connection.get("vzn", None),
                    platform=ScheduledEvent(
                        scheduled=connection.get("track", {}).get("scheduled", None),
                        actual=connection.get("track", {}).get("actual", None),
                    ),
                    destination=connection.get("station", {}).get("name", None),
                    departure=ScheduledEvent(
                        scheduled=(
                            datetime.datetime.fromtimestamp(
                                int(
                                    some_or_default(
                                        connection.get("timetable", {}).get(
                                            "scheduledDepartureTime"
                                        ),
                                        default=0,
                                    )
                                )
                                / 1000
                            )
                            if some_or_default(
                                connection.get("timetable", {}).get(
                                    "scheduledDepartureTime"
                                )
                            )
                            is not None
                            else None
                        ),
                        actual=(
                            datetime.datetime.fromtimestamp(
                                (
                                    some_or_default(
                                        connection.get("timetable", {}).get(
                                            "actualDepartureTime"
                                        ),
                                        default=0,
                                    )
                                )
                                / 1000
                            )
                            if some_or_default(
                                connection.get("timetable", {}).get(
                                    "actualDepartureTime"
                                )
                            )
                            is not None
                            else None
                        ),
                    ),
                )
                for connection in connections_json.get("connections", [])
            ]
        )
        self.store(f"connections_{station_id}", connections)
        self._connections_cache_control[station_id] = {
            "last_update": datetime.datetime.now()
        }
        yield from connections
        return


class ICEPortal(Train, StationsMixin[TrainStation]):
    """
    Wrapper for interacting with the DB ICE Portal API
    """
    _static_data = _ICEPortalStaticConnector()
    _dynamic_data = _ICEPortalDynamicConnector()

    __slots__ = []

    def now(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            int(
                some_or_default(
                    self._dynamic_data.load("status", {}).get("serverTime", None),
                    default=0,
                )
            )
            / 1000
        )

    @property
    def id(self) -> str:
        return self._dynamic_data.load("status", {}).get("tzn")

    @property
    def type(self) -> str:
        return self._dynamic_data.load("trip", {}).get("trip", {}).get("trainType")

    @property
    def number(self) -> str:
        return self._dynamic_data.load("trip", {}).get("trip", {}).get("vzn")

    @property
    def stations_dict(self) -> dict[str, TrainStation]:
        stops = self._dynamic_data.load("trip", {}).get("trip", {}).get("stops")
        if stops is None:
            raise DataInvalidError("API is missing data about stations")
        return {
            stop.get("station", {}).get("evaNr"): TrainStation(
                station_id=stop.get("station", {}).get("evaNr"),
                name=stop.get("station", {}).get("name"),
                platform=ScheduledEvent(
                    scheduled=stop.get("track", {}).get("scheduled"),
                    actual=stop.get("track", {}).get("actual"),
                ),
                arrival=ScheduledEvent(
                    scheduled=datetime.datetime.fromtimestamp(
                        int(
                            some_or_default(
                                stop.get("timetable", {}).get("scheduledArrivalTime"),
                                default=0,
                            )
                        )
                        / 1000
                    )
                    if some_or_default(
                        stop.get("timetable", {}).get("scheduledArrivalTime")
                    )
                    is not None
                    else None,
                    actual=datetime.datetime.fromtimestamp(
                        (
                            some_or_default(
                                stop.get("timetable", {}).get("actualArrivalTime"),
                                default=0,
                            )
                        )
                        / 1000
                    )
                    if some_or_default(
                        stop.get("timetable", {}).get("actualArrivalTime")
                    )
                    is not None
                    else None,
                ),
                departure=ScheduledEvent(
                    scheduled=datetime.datetime.fromtimestamp(
                        int(
                            some_or_default(
                                stop.get("timetable", {}).get("scheduledDepartureTime"),
                                default=0,
                            )
                        )
                        / 1000
                    )
                    if some_or_default(
                        stop.get("timetable", {}).get("scheduledDepartureTime")
                    )
                    is not None
                    else None,
                    actual=datetime.datetime.fromtimestamp(
                        int(
                            some_or_default(
                                stop.get("timetable", {}).get("actualDepartureTime"),
                                default=0,
                            )
                        )
                        / 1000
                    )
                    if some_or_default(
                        stop.get("timetable", {}).get("actualDepartureTime")
                    )
                    is not None
                    else None,
                ),
                position=Position(
                    latitude=stop.get("station", {})
                    .get("geocoordinates", {})
                    .get("latitude"),
                    longitude=stop.get("station", {})
                    .get("geocoordinates", {})
                    .get("longitude"),
                ),
                distance=stop.get("info", {}).get("distanceFromStart", 0),
                connections=self._dynamic_data.connections(
                    station_id=stop.get("station", {}).get("evaNr")
                ),
            )
            for stop in stops
        }

    @property
    def current_station(self) -> TrainStation:
        # Get the current station id
        stop_info = (
            self._dynamic_data.load("trip", {}).get("trip", {}).get("stopInfo", {})
        )
        station_id = some_or_default(stop_info.get("actualNext"))
        # Get the station from the stations dict
        try:
            return self.stations_dict[station_id]
        except AttributeError as e:
            raise DataInvalidError("No current station found") from e

    @property
    def speed(self) -> float:
        return kmh_to_ms(self._dynamic_data.load("status", {}).get("speed", 0))

    @property
    def distance(self) -> float:
        return self._dynamic_data.load("trip", {}).get("trip", {}).get(
            "actualPosition", 0
        ) + self._dynamic_data.load("trip", {}).get("trip", {}).get(
            "distanceFromLastStop", 0
        )

    @property
    def position(self) -> Position:
        return Position(
            self._dynamic_data.load("status", {}).get("latitude"),
            self._dynamic_data.load("status", {}).get("longitude"),
        )

    @property
    def name(self) -> str | None:
        """
        Get the name of the train.

        Most of the DB ICE train have names.
        Names are not available through the API, instead a public list of names will be used.

        :return: The name of the train
        """
        # Use unverified names as fallback, because not many verified names are available at this time
        names = self._static_data.load("train_names", {}).get("unverified_names", {})
        # overwrite the dict with verified train names
        # (There should be no conflict, but if there is a conflict use verified names)
        names.update(self._static_data.load("train_names", {}).get("names", {}))

        # The id is only the number, because formats vary between the API and printed on the side of the train
        match = re.search(r"\d+", self.id)
        # No number found, so no name is available
        if match is None:
            return None

        # Return the name, may also be None if the train has no name
        return names.get(match.group(0).lstrip("0"), None)

    def all_delay_reasons(self) -> Dict[str, Optional[List[str]]]:
        """
        Get all delay reasons for the current trip

        :return: A dictionary of delay reasons with the station id as the key
        :rtype: Dict[str, Optional[List[str]]]
        """
        return {
            stop.get("station", {}).get("evaNr", None): list(
                [
                    some_or_default(reason.get("text", None))
                    for reason in some_or_default(stop.get("delayReasons"), [])
                ]
            )
            for stop in self._dynamic_data.load("trip", {})
            .get("trip", {})
            .get("stops", [])
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
        if (
            str(
                self._dynamic_data.load("status", {}).get("bapInstalled", False)
            ).lower()
            != "true"
        ):
            return False
        # Check if the module is active
        if (
            str(self._static_data.load("bap", {}).get("status", False)).lower()
            == "true"
        ):
            return True
        return False

    def wagon_class(self) -> Literal["FIRST", "SECOND"] | None:
        """
        Get the wagon class of the wagon you are currently in

        :return: The wagon class
        :rtype: Literal["FIRST", "SECOND"]
        """
        return some_or_default(self._dynamic_data.load("status", {}).get("wagonClass"))

    def internet_connection(
        self,
    ) -> tuple[InternetStatus, InternetStatus | None, datetime.timedelta | None]:
        """
        Returns the internet connection status of the train,

        the next internet connection status,

        and the time until the change occurs.

        Be aware that some or all values can be None.

        :return: The tuple (current, next, time_remaining)
        :rtype: Tuple[InternetStatus, InternetStatus, datetime.timedelta]
        """
        remaining_seconds = (
            self._dynamic_data.load("status", {})
            .get("connectivity", {})
            .get("remainingTimeSeconds", "")
        )
        return (
            # Current state
            some_or_default(
                self._dynamic_data.load("status", {})
                .get("connectivity", {})
                .get("currentState"),
                "NO_INFO",
            ),
            # Next state
            some_or_default(
                self._dynamic_data.load("status", {})
                .get("connectivity", {})
                .get("nextState"),
                "NO_INFO",
            ),
            # Remaining time
            None
            if some_or_default(remaining_seconds) is None
            else datetime.timedelta(seconds=int(remaining_seconds)),
        )
