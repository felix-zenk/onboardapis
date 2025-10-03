from __future__ import annotations

import logging

from datetime import datetime
from enum import ReprEnum
from functools import lru_cache
from json import JSONDecodeError
from pathlib import Path
from typing import Generator, Any

import yaml

from bs4 import BeautifulSoup
from geopy import Point
from geopy.distance import distance
from requests.exceptions import ConnectTimeout
from restfly.errors import NotFoundError

from ....data import (
    ID,
    ThreadedRestAPI,
    ScheduledEvent,
    default,
    store,
    BlockingRestAPI, get_package_version,
)
from ....exceptions import APIFeatureMissingError, APIConnectionError
from ....mixins import InternetAccessInterface, InternetMetricsInterface
from ... import ConnectingTrain

logger = logging.getLogger(__name__)


class ICEPortalAPI(ThreadedRestAPI):
    API_URL = "https://iceportal.de"

    @property
    @store('train_names')
    @lru_cache
    def train_names(self) -> dict[int, str | None]:
        return yaml.safe_load((Path(__file__).parent / 'mappings.yaml').read_text(encoding='utf-8'))['names']

    @store('bap')
    @lru_cache
    def bap_service_status(self) -> dict[str, Any]:
        try:
            return self.get("bap/api/bap-service-status").json()
        except (JSONDecodeError, APIFeatureMissingError):
            return {'status': 'false'}

    @store('trip')
    def trip_info(self) -> dict[str, Any]:
        return self.get("api1/rs/tripInfo/trip").json()

    @store('status')
    def status(self) -> dict[str, Any]:
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

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def _build_session(self, **kwargs: Any) -> None:
        super()._build_session(**kwargs)
        self._session.headers.update({'X-Requested-With': 'Python/onboardapis (%s)' % get_package_version()})


class ICEPortalInternetInterface(InternetAccessInterface, InternetMetricsInterface):
    _api: ICEPortalInternetAccessAPI

    def enable(self) -> None:
        logger_before = logging.getLogger('restfly.errors.NotFoundError').disabled
        logging.getLogger('restfly.errors.NotFoundError').disabled = True
        try:
            self._api.post('cna/logon', json={}, headers={
                'X-Csrf-Token': 'csrf',
            })
        except NotFoundError:
            # old login API
            response = self._api.get('de')
            self._api.post('de/', data={
                'login': True,
                'CSRFToken': response.cookies['csrf'],
            })
        finally:
            logging.getLogger('restfly.errors.NotFoundError').disabled = logger_before

    def disable(self):
        logger_before = logging.getLogger('restfly.errors.NotFoundError').disabled
        logging.getLogger('restfly.errors.NotFoundError').disabled = True
        try:
            self._api.post('cna/logoff', json={}, headers={'X-Csrf-Token': 'csrf'})  # Not CSRF protected anymore?
        except NotFoundError:
            response = self._api.get('de/')
            self._api.post('de/', data={
                'logout': True,
                'CSRFToken': response.cookies['csrf'],
            })
        finally:
            logging.getLogger('restfly.errors.NotFoundError').disabled = logger_before

    @property
    def is_enabled(self) -> bool:
        logger_before = logging.getLogger('restfly.errors.NotFoundError').disabled
        logging.getLogger('restfly.errors.NotFoundError').disabled = True
        try:
            return self._api.get('cna/wifi/user_info').json()['result']['authenticated'] == '1'
        except NotFoundError:
            return BeautifulSoup(
                self._api.get('de').text, 'html.parser'
            ).find(id='accept') is None
        finally:
            logging.getLogger('restfly.errors.NotFoundError').disabled = logger_before

    @property
    def limit(self) -> float | None:
        try:
            usage_info = self._api.get('usage_info/')
        except APIFeatureMissingError:
            return None
        return usage_info.json()['limit']

    @property
    def used(self) -> None:
        try:
            usage_info = self._api.get('usage_info/')
        except APIFeatureMissingError:
            return None
        return usage_info.json()['used']  # TODO: verify attribute


class ModeOfTransport(str, ReprEnum):
    UNKNOWN = 'UNKNOWN'
    BUS = 'BUS'
    TRAM = 'TRAM'
    SUBWAY = 'SUBWAY'
    CITY_TRAIN = 'CITY_TRAIN'
    REGIONAL_TRAIN = 'REGIONAL_TRAIN'
    INTER_REGIONAL_TRAIN = 'INTER_REGIONAL_TRAIN'
    HIGH_SPEED_TRAIN = 'HIGH_SPEED_TRAIN'

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def local_trains(cls) -> tuple[ModeOfTransport, ...]:
        return cls.CITY_TRAIN, cls.TRAM, cls.SUBWAY

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def long_distance_trains(cls) -> tuple[ModeOfTransport, ...]:
        return cls.HIGH_SPEED_TRAIN, cls.REGIONAL_TRAIN, cls.INTER_REGIONAL_TRAIN

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def trains(cls) -> tuple[ModeOfTransport, ...]:
        # noinspection PyUnresolvedReferences
        return cls.local_trains + cls.long_distance_trains


class RegioGuideAPI(ThreadedRestAPI):
    API_URL = "https://zugportal.de"

    @store('journey')
    def journey(self) -> dict:
        return self.get("@prd/zupo-travel-information/api/public/ri/journey").json()

    def refresh(self) -> None:
        self.journey()

    @lru_cache
    def distance(self, index: int) -> float:
        """Calculate the distance from the start for the station at ``index``"""
        if index <= 0:
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
        # noinspection PyTypeChecker
        yield from (
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
            in self.get(
                f'@prd/zupo-travel-information/api/public/ri/board/departure/{station_id}',
                params=dict(
                    modeOfTransport=','.join(map(lambda m: m.value, ModeOfTransport.trains)),
                    occupancy=True
                )
            ).json().get('items', [])
        )


ZugPortalAPI = RegioGuideAPI
"""Renamed by DB. Use RegioGuideAPI instead."""


class RegioGuideInternetAccessAPI(BlockingRestAPI):
    @classmethod
    def auto_detect(cls) -> RegioGuideInternetAccessAPI:
        try:
            cls(url=RegioGuideHotsplotsInternetAccessAPI.API_URL, timeout=1., retries=0).get('auth/login.php')
            return RegioGuideHotsplotsInternetAccessAPI()
        except ConnectTimeout:
            pass

        raise NotImplementedError


class RegioGuideHotsplotsInternetAccessAPI(RegioGuideInternetAccessAPI):
    API_URL = 'http://192.168.44.1'

    def enable(self) -> None:
        response = self.get('auth/login.php')
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find(name='form')
        if form is None:
            raise APIConnectionError('Internet access login form not found')
        response = self.post('auth/login.php', data={
            "haveTerms": form.find(attrs={'name': 'haveTerms'}).attrs['value'],
            "termsOK": form.find(attrs={'name': 'termsOK'}).attrs['value'],
            "button": form.find(attrs={'name': 'button'}).get_text(),
            "challenge": form.find(attrs={'name': 'challenge'}).attrs['value'],
            "uamip": form.find(attrs={'name': 'uamip'}).attrs['value'],
            "uamport": form.find(attrs={'name': 'uamport'}).attrs['value'],
            "userurl": form.find(attrs={'name': 'userurl'}).attrs['value'],
            "myLogin": form.find(attrs={'name': 'myLogin'}).attrs['value'],
            "ll": form.find(attrs={'name': 'll'}).attrs['value'],
            "nasid": form.find(attrs={'name': 'nasid'}).attrs['value'],
            "custom": form.find(attrs={'name': 'custom'}).attrs['value'],
        })
        response.raise_for_status()

    def disable(self) -> None:
        self.get('logoff').raise_for_status()  # Not CSRF protected!


class RegioGuideInternetAccessInterface(InternetAccessInterface):
    _api: RegioGuideHotsplotsInternetAccessAPI

    def __init__(self, api: RegioGuideInternetAccessAPI):
        super().__init__(api)

    def enable(self) -> None:
        """WIP: does not work yet"""
        self._api.enable()

    def disable(self) -> None:
        """WIP: does not work yet"""
        self._api.disable()

    @property
    def is_enabled(self) -> bool:
        """WIP: does not work reliably yet"""
        response = self._api.get('/auth/login.php')
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.select_one('[href*="/logoff"]') is not None
