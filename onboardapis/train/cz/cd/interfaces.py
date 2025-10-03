from __future__ import annotations

import logging

from functools import lru_cache
from json import JSONDecodeError

from .schema import CdObpInfoSchema, CdObpConnectivitySchema, CdObpRealtimeSchema, CdObpCurrentSchema
from ....data import store, ThreadedRestAPI
from ....exceptions import APIFeatureMissingError

logger = logging.getLogger(__name__)


class OnBoardPortalAPI(ThreadedRestAPI):
    # noinspection HttpUrlsUsage
    API_URL = 'http://cdwifi.cz/portal/api'

    @store('info')
    def info(self) -> CdObpInfoSchema | None:
        try:
            return self.get('/vehicle/info').json()
        except (JSONDecodeError, APIFeatureMissingError):
            return None

    @store('user')
    def user(self) -> CdObpInfoSchema | None:
        try:
            return self.get('/vehicle/gateway/user').json()
        except (JSONDecodeError, APIFeatureMissingError):
            return None

    @store('connectivity')
    def connectivity(self) -> CdObpConnectivitySchema | None:
        try:
            return self.get('/vehicle/gateway/connectivity').json()
        except (JSONDecodeError, APIFeatureMissingError):
            return None

    @store('realtime')
    def realtime(self) -> CdObpRealtimeSchema | None:
        try:
            return self.get('/vehicle/realtime').json()
        except (JSONDecodeError, APIFeatureMissingError):
            return None

    @store('current')
    def current(self) -> CdObpCurrentSchema | None:
        try:
            return self.get('/timetable/connexion/current').json()
        except (JSONDecodeError, APIFeatureMissingError):
            return None

    @store('line')
    def line(self) -> dict | None:
        try:
            return self.get('/timetable/route/line').json()
        except (JSONDecodeError, APIFeatureMissingError):
            return None

    @store('advertisement_type')
    @lru_cache
    def advertisement_type(self) -> dict | None:
        try:
            return self.get('/advertisement/type').json()
        except (JSONDecodeError, APIFeatureMissingError):
            return None

    def refresh(self) -> None:
        self.current()
        self.info()
        self.realtime()
