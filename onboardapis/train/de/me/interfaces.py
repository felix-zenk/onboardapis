from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from ....exceptions import APIConnectionError
from ....data import BlockingRestAPI
from ....mixins import InternetAccessInterface

logger = logging.getLogger(__name__)


class MetronomAPI(BlockingRestAPI):
    # noinspection HttpUrlsUsage
    API_URL = 'http://wifi.metronom.de'


class MetronomInternetAccessInterface(BlockingRestAPI, InternetAccessInterface):
    # noinspection HttpUrlsUsage
    API_URL = 'http://wifi.metronom.de'

    def enable(self):
        response = self.get('de')
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find(class_='user-offline') is None:
            return  # Already online

        # csrf_token = soup.find('input', {'name': 'CSRFToken'})['value']
        csrf_token = response.cookies['csrf']
        response = self.post('de', data={
            'login': True,
            'CSRFToken': csrf_token,
        })
        response.raise_for_status()
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-online') is None:
            raise APIConnectionError('Login failed!')

    def disable(self):
        response = self.get('de')
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.find(class_='user-online') is None:
            return  # Already offline

        # csrf_token = soup.find('input', {'name': 'CSRFToken'})['value']
        csrf_token = response.cookies['csrf']
        response = self.post('de', data={
            'logout': True,
            'CSRFToken': csrf_token,
        })
        response.raise_for_status()
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-offline') is None:
            raise APIConnectionError('Logout failed!')

    @property
    def is_enabled(self) -> bool:
        return BeautifulSoup(
            self.get('de').text, 'html.parser'
        ).find(class_='user-offline') is None
