from __future__ import annotations

import json
import logging

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from gql import gql
from requests.exceptions import ConnectionError

from ....exceptions import InitialConnectionError
from ....data import ThreadedGraphQlAPI, get_package_version, store
from ....mixins import InternetAccessInterface

logger = logging.getLogger(__name__)


class GenericUnwiredAPI(ThreadedGraphQlAPI):
    API_URL = 'https://wasabi-splashpage.wifi.unwired.at/api/graphql'

    _user_session_id: str
    _journey_widget_id: str

    def __init__(self):
        ThreadedGraphQlAPI.__init__(self, queries={
            'splash_page': (Path(__file__).parent / 'queries' / 'splash_page.graphql').read_text(encoding='utf-8'),
            'journey_info': (Path(__file__).parent / 'queries' / 'journey_info.graphql').read_text(encoding='utf-8'),
        })

    def init(self):
        try:
            response = requests.get(
                'https://unwired.info/?source=wasabi',
                headers={'User-Agent': 'Python/onboardapis (%s)' % get_package_version()}
            )
            self._user_session_id, *_ = parse_qs(urlparse(response.url).query)['user_session_id']
            self._journey_widget_id = '363a8707-5e3e-4a5b-b565-9d22470dfd25'
            # journey_page, *_ = *filter(lambda page: page['page_id'] == 'ec6b0ec5-b78e-453c-9cb0-683d57f3cb13', self.splash_page()['splashpage']['pages']), None  # TODO
            # if not journey_page:
            #    raise InitialConnectionError
            # widget, *_ = *filter(lamdbda widget: widget['__typename'] == 'JourneyInfoWidget', journey_page['widgets']), None
            # if not widget:
            #    raise InitialConnectionError
            # self._journey_widget_id = widget['widget_id']
        except (ConnectionError, KeyError) as e:
            raise InitialConnectionError from e

    def splash_page(self) -> dict:
        response = self.execute(
            document=gql(self.queries['splash_page']),
            variable_values={
                "user_session_id": self._user_session_id,
                "language": "de",
                "initial": False
            }
        )
        return response

    @store('journey')
    def journey(self) -> dict:
        response = self.execute(
            document=gql(self.queries['journey_info']),
            variable_values={
                "widget_id": self._journey_widget_id,
                "language": "de",
                "user_session_id": self._user_session_id,
            }
        )
        journey = json.loads(response['feed_widget']['widget']['json'])
        if 'course' not in journey:
            return {}
        return journey['course']

    def refresh(self) -> None:
        self.journey()


class GenericUnwiredInternetAccessInterface(InternetAccessInterface):
    def enable(self) -> None:  # TODO: implement
        pass

    def disable(self) -> None:  # TODO: implement
        pass
