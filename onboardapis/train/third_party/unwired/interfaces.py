from __future__ import annotations

import json
import logging

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from gql import gql
from requests.exceptions import ConnectionError

from ....exceptions import InitialConnectionError, APIConnectionError
from ....data import ThreadedGraphQlAPI, get_package_version, store
from ....mixins import InternetAccessInterface

logger = logging.getLogger(__name__)


class GenericUnwiredAPI(ThreadedGraphQlAPI):
    API_URL = 'https://wasabi-splashpage.wifi.unwired.at/api/graphql'

    _user_session_id: str
    _journey_widget_id: str
    _connect_widget_id: str

    def __init__(self):
        ThreadedGraphQlAPI.__init__(self, queries={
            'splash_page': (Path(__file__).parent / 'queries' / 'splash_page.graphql').read_text(encoding='utf-8'),
            'journey_info': (Path(__file__).parent / 'queries' / 'journey_info.graphql').read_text(encoding='utf-8'),
            'geo_points': (Path(__file__).parent / 'queries' / 'geo_points.graphql').read_text(encoding='utf-8'),
        })

    def init(self):
        try:
            response = requests.get(
                'https://unwired.info/?source=wasabi',
                headers={'User-Agent': 'Python/onboardapis (%s)' % get_package_version()}
            )
            self._user_session_id, *_ = parse_qs(urlparse(response.url).query)['user_session_id']
            self._journey_widget_id = '363a8707-5e3e-4a5b-b565-9d22470dfd25'
            self._connect_widget_id = 'b052e62c-bb87-43fb-a0ab-f0cfe05adfef'
            # journey_page, *_ = *filter(lambda page: page['page_id'] == 'ec6b0ec5-b78e-453c-9cb0-683d57f3cb13', self.splash_page()['pages']), None  # noqa: E501  # TODO
            # if not journey_page:
            #    raise InitialConnectionError
            # widget, *_ = *filter(lamdbda widget: widget['__typename'] == 'JourneyInfoWidget', journey_page['widgets']), None  # noqa: E501
            # if not widget:
            #    raise InitialConnectionError
            # self._journey_widget_id = widget['widget_id']
        except (ConnectionError, KeyError) as e:
            raise InitialConnectionError from e

    def splash_page(self) -> dict:
        return self.execute(
            document=gql(self.queries['splash_page']),
            variable_values={
                "user_session_id": self._user_session_id,
                "language": "de",
                "initial": False
            }
        )['splashpage']

    @store('geo_points')
    def geo_points(self) -> dict:
        response = self.execute(
            document=gql(self.queries['geo_points']),
            variable_values={
                "widget_id": self._journey_widget_id,
                "user_session_id": self._user_session_id,
            }
        )['feed_widget']
        if 'error' in response:
            logger.debug(
                'Got an error while requesting journey information: %s - %s',
                response['error']['error_code'],
                response['error']['error_message']
            )
            return {}
        return response['widget']['geo_points']

    @store('journey')
    def journey(self) -> dict:
        response = self.execute(
            document=gql(self.queries['journey_info']),
            variable_values={
                "widget_id": self._journey_widget_id,
                "user_session_id": self._user_session_id,
            }
        )['feed_widget']
        if 'error' in response:
            logger.debug(
                'Got an error while requesting journey information: %s - %s',
                response['error']['error_code'],
                response['error']['error_message']
            )
            return {}
        journey = json.loads(response['widget']['json'])
        if 'course' not in journey:
            return {}
        return journey['course']

    def refresh(self) -> None:
        self.journey()


class GenericUnwiredInternetAccessInterface(InternetAccessInterface):
    _api: GenericUnwiredAPI

    def __init__(self, api: GenericUnwiredAPI) -> None:
        super().__init__(api)
        self._api.queries.update({
            'client_connect': (
                Path(__file__).parent / 'mutations' / 'client_connect.graphql'
            ).read_text(encoding='utf-8'),
            'client_logout': (
                Path(__file__).parent / 'mutations' / 'client_logout.graphql'
            ).read_text(encoding='utf-8'),
            'online_status': (
                Path(__file__).parent / 'queries' / 'online_status.graphql'
            ).read_text(encoding='utf-8'),
        })

    def enable(self) -> None:  # TODO: implement
        # noinspection PyProtectedMember
        response = self._api.execute(
            document=gql(self._api.queries['client_connect']),
            variable_values={
                "user_session_id": self._api._user_session_id,
                "widget_id": self._api._connect_widget_id,
            }
        )
        if response['state'] != '':  # TODO
            raise APIConnectionError('Login failed!')

    def disable(self) -> None:  # TODO: implement
        # noinspection PyProtectedMember
        response = self._api.execute(
            document=gql(self._api.queries['client_logout']),
            variable_values={
                "user_session_id": self._api._user_session_id,
            }
        )
        if response['state'] != '':  # TODO
            raise APIConnectionError('Login failed!')

    @property
    def is_enabled(self) -> bool:  # TODO: implement
        return self._api.splash_page()['online']
