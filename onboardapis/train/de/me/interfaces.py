from __future__ import annotations

import logging
from typing import Any

from bs4 import BeautifulSoup

from ....exceptions import APIConnectionError
from ....data import BlockingRestAPI, API
from ....mixins import InternetAccessInterface

logger = logging.getLogger(__name__)


class MetronomAPI(BlockingRestAPI):
    # noinspection HttpUrlsUsage
    API_URL = 'http://wifi.metronom.de'


class MetronomInternetAccessInterface(InternetAccessInterface):
    _api: BlockingRestAPI

    # noinspection HttpUrlsUsage
    API_URL = 'http://wifi.metronom.de'

    def __init__(self, api: BlockingRestAPI) -> None:
        InternetAccessInterface.__init__(self, api)

    def enable(self):
        response = self._api.get('de')
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find(class_='user-offline') is None:
            return  # Already online

        csrf_token = response.cookies['csrf']
        response = self._api.post('de/', data={
            'login': True,
            'CSRFToken': csrf_token,
        })
        response.raise_for_status()
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-online') is None:
            raise APIConnectionError('Login failed!')

    def disable(self):
        response = self._api.get('de')
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find(class_='user-online') is None:
            return  # Already offline

        csrf_token = response.cookies['csrf']
        response = self._api.post('de/', data={
            'logout': True,
            'CSRFToken': csrf_token,
        })
        response.raise_for_status()
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-offline') is None:
            raise APIConnectionError('Logout failed!')

    @property
    def is_enabled(self) -> bool:
        return BeautifulSoup(
            self._api.get('de').text, 'html.parser'
        ).find(class_='user-online') is not None
