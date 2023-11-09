"""
Implementation for the german operator DB (Deutsche Bahn).
"""
from __future__ import annotations

import datetime
import re

from typing import Tuple, Dict, List, Optional, Literal

from .connectors import (
    ICEPortalStaticConnector,
    ICEPortalDynamicConnector,
    ZugPortalStaticConnector,
    ZugPortalDynamicConnector,
)
from .mappings import id_name_map
from ... import Train, TrainStation
from ....mixins import StationsMixin
from ....exceptions import DataInvalidError
from ....conversions import kmh_to_ms
from ....data import (
    default,
    ScheduledEvent,
    Position,
)
from ...._types import ID

InternetStatus = Literal["NO_INFO", "NO_INTERNET", "UNSTABLE", "WEAK", "MIDDLE", "HIGH"]


class ICEPortal(Train, StationsMixin[TrainStation]):
    """
    Wrapper for interacting with the DB ICE Portal API
    """

    _static_data = ICEPortalStaticConnector()
    _dynamic_data = ICEPortalDynamicConnector()

    __slots__ = []

    def now(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            int(
                default(
                    self._dynamic_data.load("status", {}).get("serverTime", None),
                    __default=0,
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
                            default(
                                stop.get("timetable", {}).get("scheduledArrivalTime"),
                                __default=0,
                            )
                        )
                        / 1000
                    )
                    if default(
                        stop.get("timetable", {}).get("scheduledArrivalTime")
                    )
                       is not None
                    else None,
                    actual=datetime.datetime.fromtimestamp(
                        (
                            default(
                                stop.get("timetable", {}).get("actualArrivalTime"),
                                __default=0,
                            )
                        )
                        / 1000
                    )
                    if default(
                        stop.get("timetable", {}).get("actualArrivalTime")
                    )
                       is not None
                    else None,
                ),
                departure=ScheduledEvent(
                    scheduled=datetime.datetime.fromtimestamp(
                        int(
                            default(
                                stop.get("timetable", {}).get("scheduledDepartureTime"),
                                __default=0,
                            )
                        )
                        / 1000
                    )
                    if default(
                        stop.get("timetable", {}).get("scheduledDepartureTime")
                    )
                       is not None
                    else None,
                    actual=datetime.datetime.fromtimestamp(
                        int(
                            default(
                                stop.get("timetable", {}).get("actualDepartureTime"),
                                __default=0,
                            )
                        )
                        / 1000
                    )
                    if default(
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
        station_id = default(stop_info.get("actualNext"))
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
        match = re.search(r"\d+", f'{self.id}')
        if match is None:
            return None

        return id_name_map.get(int(match.group(0)))

    @property
    def all_delay_reasons(self) -> Dict[str, Optional[List[str]]]:
        """
        Get all delay reasons for the current trip

        :return: A dictionary of delay reasons with the station id as the key
        :rtype: Dict[str, Optional[List[str]]]
        """
        return {
            stop.get("station", {}).get("evaNr", None): list(
                [
                    default(reason.get("text", None))
                    for reason in default(stop.get("delayReasons"), [])
                ]
            )
            for stop in self._dynamic_data.load("trip", {})
            .get("trip", {})
            .get("stops", [])
        }

    @property
    def delay_reasons(self) -> Optional[List[str]]:
        """
        Get the delay reason for the current station

        :return: The delay reason
        :rtype: Optional[List[str]]
        """
        return self.all_delay_reasons.get(self.current_station.id, None)

    @property
    def has_bap(self) -> bool:
        """
        Returns True if the train has a BAP module installed and active

        bap = 'Bestellen am Platz' is a service that allows passengers to order food and drinks right to their seat

        :return:
        """
        # bap is a service exclusive to first class
        if self.wagon_class != "FIRST":
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

    @property
    def wagon_class(self) -> Literal["FIRST", "SECOND"] | None:
        """
        Get the wagon class of the wagon you are currently in

        :return: The wagon class
        :rtype: Literal["FIRST", "SECOND"]
        """
        return default(self._dynamic_data.load("status", {}).get("wagonClass"))

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
            default(
                self._dynamic_data.load("status", {})
                .get("connectivity", {})
                .get("currentState"),
                "NO_INFO",
            ),
            # Next state
            default(
                self._dynamic_data.load("status", {})
                .get("connectivity", {})
                .get("nextState"),
                "NO_INFO",
            ),
            # Remaining time
            None
            if default(remaining_seconds) is None
            else datetime.timedelta(seconds=int(remaining_seconds)),
        )


class ZugPortal(Train):
    """
    Wrapper for interacting with the DB Zug Portal API
    """

    _static_data = ZugPortalStaticConnector()
    _dynamic_data = ZugPortalDynamicConnector()

    @property
    def type(self) -> str:
        pass

    @property
    def number(self) -> str:
        pass

    @property
    def distance(self) -> float:
        pass

    @property
    def id(self) -> ID:
        pass

    @property
    def position(self) -> Position:
        pass

    @property
    def speed(self) -> float:
        pass
