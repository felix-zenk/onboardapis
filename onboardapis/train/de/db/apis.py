from __future__ import annotations

import logging
import re

from typing import Literal
from datetime import datetime, timedelta

from typing_extensions import deprecated

from ....exceptions import DataInvalidError
from ....data import ID, default, ScheduledEvent, Position
from ....mixins import SpeedMixin, PositionMixin, StationsMixin, InternetAccessMixin
from ....units import ms
from ... import Train, TrainStation
from .mappings import id_name_map
from .interfaces import ICEPortalAPI, RegioGuideAPI, ICEPortalInternetInterface

logger = logging.getLogger(__name__)

InternetStatus = Literal["NO_INFO", "NO_INTERNET", "UNSTABLE", "WEAK", "MIDDLE", "HIGH"]


class ICEPortal(Train, SpeedMixin, PositionMixin, StationsMixin[TrainStation], InternetAccessMixin):
    """Wrapper for interacting with the DB ICE Portal API."""

    _api: ICEPortalAPI
    _internet_access: ICEPortalInternetInterface

    def __init__(self):
        self._api = ICEPortalAPI()
        self._internet_access = ICEPortalInternetInterface(self._api)
        Train.__init__(self)

    def now(self) -> datetime:
        return datetime.fromtimestamp(int(default(
            self._api["status"].get("serverTime", None), 0,
        )) / 1000)

    @property
    def id(self) -> str:
        return self._api["status"].get("tzn")

    @property
    def type(self) -> str:
        return self._api["trip"].get("trip", {}).get("trainType")

    @property
    def line_number(self) -> str:
        return self._api["trip"].get("trip", {}).get("vzn")

    @property
    def stations_dict(self) -> dict[str, TrainStation]:
        stops = self._api["trip"].get("trip", {}).get("stops")
        if stops is None:
            raise DataInvalidError("API is missing data about stations")
        return {
            stop.get("station", {}).get("evaNr"): TrainStation(
                id=stop.get("station", {}).get("evaNr"),
                name=stop.get("station", {}).get("name"),
                platform=ScheduledEvent(
                    scheduled=stop.get("track", {}).get("scheduled"),
                    actual=stop.get("track", {}).get("actual"),
                ),
                arrival=ScheduledEvent(
                    scheduled=datetime.fromtimestamp(int(default(
                        stop.get("timetable", {}).get("scheduledArrivalTime"), 0,
                    )) / 1000)
                    if default(stop.get("timetable", {}).get("scheduledArrivalTime")) is not None
                    else None,
                    actual=datetime.fromtimestamp((default(
                        stop.get("timetable", {}).get("actualArrivalTime"), 0,
                    )) / 1000)
                    if default(stop.get("timetable", {}).get("actualArrivalTime")) is not None
                    else None,
                ),
                departure=ScheduledEvent(
                    scheduled=datetime.fromtimestamp(int(default(
                        stop.get("timetable", {}).get("scheduledDepartureTime"), 0,
                    )) / 1000)
                    if default(stop.get("timetable", {}).get("scheduledDepartureTime")) is not None
                    else None,
                    actual=datetime.fromtimestamp(int(default(
                        stop.get("timetable", {}).get("actualDepartureTime"), 0,
                    )) / 1000)
                    if default(stop.get("timetable", {}).get("actualDepartureTime")) is not None
                    else None,
                ),
                position=Position(
                    latitude=stop.get("station", {}).get("geocoordinates", {}).get("latitude"),
                    longitude=stop.get("station", {}).get("geocoordinates", {}).get("longitude"),
                ),
                distance=stop.get("info", {}).get("distanceFromStart", 0),
                _connections=self._api.get_connections(station_id=stop.get("station", {}).get("evaNr")),
            )
            for stop in stops
        }

    @property
    def current_station(self) -> TrainStation:
        # Get the current station id
        stop_info = (
            self._api["trip"].get("trip", {}).get("stopInfo", {})
        )
        station_id = default(stop_info.get("actualNext"))
        # Get the station from the stations dict
        try:
            return self.stations_dict[station_id]
        except KeyError as e:
            raise DataInvalidError("No current station found") from e

    @property
    def speed(self) -> float:
        return ms(kmh=self._api["status"].get("speed", 0))

    @property
    def distance(self) -> float:
        return (
            self._api["trip"].get("trip", {}).get("actualPosition", 0)
            + self._api["trip"].get("trip", {}).get("distanceFromLastStop", 0)
        )

    @property
    def position(self) -> Position:
        return Position(
            latitude=self._api["status"].get("latitude"),
            longitude=self._api["status"].get("longitude"),
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
    def all_delay_reasons(self) -> dict[str, list[str]]:
        """
        Get all delay reasons for the current trip

        :return: A dictionary of delay reasons with the station id as the key
        :rtype: dict[str, list[str] | None]
        """
        return {
            stop.get("station", {}).get("evaNr", None): list(
                [
                    default(reason.get("text", None))
                    for reason in default(stop.get("delayReasons"), [])
                ]
            )
            for stop in self._api["trip"]
            .get("trip", {})
            .get("stops", [])
        }

    @property
    def delay_reasons(self) -> list[str] | None:
        """
        Get the delay reason for the current station

        :return: The delay reason
        :rtype: list[str] | None
        """
        return self.all_delay_reasons.get(self.current_station.id, None)

    @property
    def has_bap(self) -> bool:
        """
        Returns True if the train has a BAP module installed and active

        bap = 'Bestellen am Platz' is a service that allows passengers to order food and drinks right to their seat
        """
        # bap is a service exclusive to first class
        if self.wagon_class != "FIRST":
            return False
        # Check if the module is installed
        if str(self._api["status"].get("bapInstalled", False)).lower() != "true":
            return False
        # Check if the module is active
        return str(self._api["bap"].get("status", False)).lower() == "true"

    @property
    def wagon_class(self) -> Literal["FIRST", "SECOND"] | None:
        """
        Get the wagon class of the wagon you are currently in

        :return: The wagon class
        :rtype: Literal["FIRST", "SECOND"]
        """
        return default(self._api["status"].get("wagonClass"))

    @property
    def current_internet_status(self) -> InternetStatus:
        """Returns the current internet connection status of the train."""
        return default(
            self._api["status"]
            .get("connectivity", {})
            .get("currentState"),
            "NO_INFO",
        )

    @property
    def next_internet_status(self) -> InternetStatus:
        """Returns the next internet connection status of the train."""
        return default(
            self._api["status"]
            .get("connectivity", {})
            .get("nextState"),
            "NO_INFO",
        )

    @property
    def internet_status_change(self) -> timedelta | None:
        """Returns the timedelta until ``internet_status`` changes to ``next_internet_status``."""
        remaining_seconds = (
            self._api["status"]
            .get("connectivity", {})
            .get("remainingTimeSeconds", "")
        )
        return None if default(remaining_seconds) is None else timedelta(seconds=int(remaining_seconds))


class RegioGuide(Train, StationsMixin[TrainStation]):
    """Wrapper for interacting with the DB Regio-Guide API, formerly Zug Portal."""

    _api: RegioGuideAPI

    def __init__(self):
        self._api = RegioGuideAPI()
        Train.__init__(self)

    @property
    def id(self) -> ID:
        return self._api['journey'].get('no')

    @property
    def type(self) -> str:
        return self._api['journey'].get('category')

    @property
    def line_number(self) -> str:
        return self._api['journey'].get('name').lstrip(self.type).strip()

    @property
    def stations_dict(self) -> dict[ID, TrainStation]:
        return {
            stop.get('station', {}).get('evaNo'): TrainStation(
                id=stop.get('station', {}).get('evaNo'),
                name=stop.get('station', {}).get('name'),
                platform=ScheduledEvent(
                    scheduled=stop.get('track', {}).get('target'),
                    actual=stop.get('track', {}).get('prediction')
                ),
                arrival=None if stop.get('arrivalTime') is None else ScheduledEvent(
                    scheduled=datetime.fromtimestamp(stop.get('arrivalTime', {}).get('targetTimeInMs', 0)),
                    actual=datetime.fromtimestamp(stop.get('arrivalTime', {}).get('predictedTimeInMs', 0))
                ),
                departure=None if stop.get('departureTime') is None else ScheduledEvent(
                    scheduled=datetime.fromtimestamp(stop.get('departureTime', {}).get('targetTimeInMs', 0)),
                    actual=datetime.fromtimestamp(stop.get('departureTime', {}).get('predictedTimeInMs', 0))
                ),
                position=Position(
                    latitude=stop.get('station', {}).get('position', {}).get('latitude'),
                    longitude=stop.get('station', {}).get('position', {}).get('longitude')
                ),
                distance=self._api.distance(index),
                _connections=self._api.connections(stop.get('station', {}).get('evaNo')),
            )
            for index, stop in enumerate(self._api['journey'].get('stops', []))
        }

    @property
    def current_station(self) -> TrainStation:
        station, *_ = (*filter(
            lambda s: self.now < default(s.arrival.actual, s.departure.actual),
            self.stations
        ), None)
        return self.destination if station is None else station


ZugPortal = deprecated('Renamed by DB. Use RegioGuide instead.')(RegioGuide)
"""Renamed by DB. Use RegioGuide instead."""
