from __future__ import annotations

import logging

from datetime import datetime
from enum import Enum
from functools import lru_cache
from http import HTTPStatus
from typing import Generator

from geopy import Point
from geopy.distance import distance

from ....data import (
    ID,
    ThreadedRestAPI,
    ScheduledEvent,
    default,
    store,
    BlockingRestAPI, get_package_version,
)
from ....mixins import InternetAccessInterface, InternetMetricsInterface
from ... import ConnectingTrain

logger = logging.getLogger(__name__)


class ICEPortalAPI(ThreadedRestAPI):
    API_URL = "https://iceportal.de"

    @store('bap')
    @lru_cache
    def bap_service_status(self) -> dict[str, any]:
        return self.get("bap/api/bap-service-status").json()

    @store('trip')
    def trip_info(self) -> dict[str, any]:
        return self.get("api1/rs/tripInfo/trip").json()

    @store('status')
    def status(self) -> dict[str, any]:
        return self.get("api1/rs/status").json()

    def refresh(self) -> None:
        self.status()
        self.trip_info()
        self.bap_service_status()

    def get_connections(
        self, station_id: str
    ) -> Generator[ConnectingTrain, None, None]:
        """
        Get all connections for a station

        :param station_id: The station to get the connections for
        :type station_id: str
        :return: A generator yielding a list of connections for the station
        :rtype: Generator[list[ConnectingTrain]]
        """
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
                            datetime.fromtimestamp(int(default(
                                connection.get("timetable", {}).get("scheduledDepartureTime"), 0,
                            )) / 1000)
                            if default(connection.get("timetable", {}).get("scheduledDepartureTime")) is not None
                            else None
                        ),
                        actual=(
                            datetime.fromtimestamp(int(default(
                                connection.get("timetable", {}).get("actualDepartureTime"), 0
                            )) / 1000)
                            if default(connection.get("timetable", {}).get("actualDepartureTime")) is not None
                            else None
                        ),
                    ),
                )
                for connection in self.get(f"/api1/rs/tripInfo/connection/{station_id}").json().get("connections", [])
            ]
        )
        if len(connections) == 0:  # no data available
            cached = self._data.get(f"connections_{station_id}", [])
            yield from cached
            return

        self[f"connections_{station_id}"] = connections
        yield from connections
        return


class ICEPortalInternetAccessAPI(BlockingRestAPI):
    API_URL = 'https://login.wifionice.de'

    def _build_session(self, **kwargs: any) -> None:
        super()._build_session(**kwargs)
        self._session.headers['X-Requested-With'] = 'Python/onboardapis (%s)' % get_package_version(),


class ICEPortalInternetInterface(InternetAccessInterface, InternetMetricsInterface):
    _api: ICEPortalInternetAccessAPI

    def enable(self) -> None:
        """WIP: DOES NOT WORK YET!"""
        response = self._api.post('cna/logon', json={}, headers={
            'X-Csrf-Token': 'csrf',
        })
        if response.status_code != HTTPStatus.NOT_FOUND:
            response.raise_for_status()
            return

        # TODO: Response
        logger.error('API difference!')
        response.raise_for_status()

    def disable(self):
        """WIP: DOES NOT WORK YET!"""
        response = self._api.post('cna/logoff', json={}, headers={'X-Csrf-Token': 'csrf'})
        if response.status_code != HTTPStatus.NOT_FOUND:
            response.raise_for_status()
            return

        # TODO: response
        logger.error('API difference!')
        response.raise_for_status()

    @property
    def is_enabled(self) -> bool:
        return self._api.get('cna/wifi/user_info').json()['result']['authenticated'] == '1'

    def limit(self) -> float | None:
        usage_info = self._api.get('usage_info')
        if usage_info.status_code == HTTPStatus.NOT_IMPLEMENTED:
            return None
        return usage_info.json()['limit']  # TODO min api version = 14?


class ModeOfTransport(str, Enum):
    UNKNOWN = 'UNKNOWN'
    BUS = 'BUS'
    TRAM = 'TRAM'
    SUBWAY = 'SUBWAY'
    CITY_TRAIN = 'CITY_TRAIN'
    REGIONAL_TRAIN = 'REGIONAL_TRAIN'
    INTER_REGIONAL_TRAIN = 'INTER_REGIONAL_TRAIN'
    HIGH_SPEED_TRAIN = 'HIGH_SPEED_TRAIN'

    @property
    def local_trains(self) -> tuple[ModeOfTransport, ...]:
        return self.CITY_TRAIN, self.TRAM, self.SUBWAY

    @property
    def long_distance_trains(self) -> tuple[ModeOfTransport, ...]:
        return self.HIGH_SPEED_TRAIN, self.REGIONAL_TRAIN, self.INTER_REGIONAL_TRAIN

    @property
    def trains(self) -> tuple[ModeOfTransport, ...]:
        return self.local_trains + self.long_distance_trains


class RegioGuideAPI(BlockingRestAPI):
    API_URL = "https://regio-guide.de"

    @store('journey')
    def journey(self):
        return self.get("@prd/zupo-travel-information/api/public/ri/journey").json()

    def refresh(self) -> None:
        self.journey()

    @lru_cache
    def distance(self, index: int) -> float:
        """Calculate the distance from the start for the station at index ``index``"""
        if index == 0:
            return 0.0

        start = self._data['journey'].get('stops', [])[0]
        stop = self._data['journey'].get('stops', [])[index]

        return self.distance(index - 1) + distance(Point(
            latitude=start.get('station', {}).get('position', {}).get('latitude'),
            longitude=start.get('station', {}).get('position', {}).get('longitude')
        ), Point(
            latitude=stop.get('station', {}).get('position', {}).get('latitude'),
            longitude=stop.get('station', {}).get('position', {}).get('longitude')
        )).meters

    def connections(self, station_id: ID) -> Generator[ConnectingTrain, None, None]:
        departure_board = self.get(
            f'@prd/zupo-travel-information/api/public/ri/board/departure/{station_id}',
            params=dict(
                modeOfTransport=','.join(mode.value for mode in ModeOfTransport.trains),  # type: ignore
                occupancy=True
            )
        )
        return (
            ConnectingTrain(
                departure=ScheduledEvent(
                    scheduled=datetime.fromisoformat(item['timePredicted']),
                    actual=datetime.fromisoformat(item['time'])
                ),
                destination=item['station']['name'],
                line_number=item['train']['lineName'],
                platform=ScheduledEvent(
                    scheduled=item['platformPredicted'],
                    actual=item['platform'],
                ),
                vehicle_type=item['train']['category'],
            )
            for item
            in departure_board.get('items', [])
        )


ZugPortalAPI = RegioGuideAPI
"""Renamed by DB. Use RegioGuideAPI instead."""
