from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from ....data import BlockingRestAPI
from ....exceptions import APIConnectionError
from ....mixins import InternetAccessInterface

logger = logging.getLogger(__name__)


class GenericIcomeraAPI(BlockingRestAPI):
    # noinspection HttpUrlsUsage
    API_URL = 'http://omboard.info'


class GenericIcomeraInternetAccessInterface(InternetAccessInterface):
    _api: BlockingRestAPI

    def __init__(self, api: BlockingRestAPI) -> None:
        InternetAccessInterface.__init__(self, api)

    def enable(self) -> None:
        response = self._api.get('de')
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-offline') is None:
            return  # Already online

        response = self._api.post('de/', data={
            'login': True,
            'CSRFToken': response.cookies['csrf'],
        })
        response.raise_for_status()
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-online') is None:
            raise APIConnectionError('Login failed!')

    def disable(self) -> None:
        response = self._api.get('de')
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-online') is None:
            return  # Already offline

        response = self._api.post('de/', data={
            'logout': True,
            'CSRFToken': response.cookies['csrf'],
        })
        response.raise_for_status()
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-offline') is None:
            raise APIConnectionError('Logout failed!')

    @property
    def is_enabled(self) -> bool:
        return BeautifulSoup(
            self._api.get('de').text, 'html.parser'
        ).find(class_='user-online') is not None
