from __future__ import annotations

import json
import logging
import requests

from typing import ClassVar
from urllib.parse import parse_qs, urlparse

from gql import gql

from ....exceptions import InitialConnectionError
from ....data import ThreadedGraphQlAPI, get_package_version
from ....mixins import InternetAccessInterface

logger = logging.getLogger(__name__)


class GenericUnwiredAPI(ThreadedGraphQlAPI):
    API_URL = 'https://wasabi-splashpage.wifi.unwired.at/api/graphql'
    UNWIRED_GRAPHQL_QUERY: ClassVar[str] = '''
    query feed_widget($user_session_id: ID, $ap_mac: String, $widget_id: ID!, $language: String) {
          feed_widget(
            user_session_id: $user_session_id
            ap_mac: $ap_mac
            widget_id: $widget_id
            language: $language
          ) {
            user_session_id
            error {
              ...Error
              __typename
            }
            widget {
              ...Widget
              __typename
            }
            __typename
          }
        }
        fragment Error on Error {
          error_code
          error_message
          __typename
        }
        fragment Widget on Widget {
          widget_id
          page_id
          position
          date_updated
          ... on SimpleTextWidget {
            is_ready
            ...SimpleTextWidget
            __typename
          }
          ... on ConnectWidget {
            button_text
            connected_text
            variant
            confirmation
            delay
            require_sms_auth
            email_mandatory
            terms_of_service
            store_terms
            enable_anchor
            anchor {
              ...Anchor
              __typename
            }
            __typename
          }
          ... on JourneyInfoWidget {
            json
            enable_anchor
            anchor {
              ...Anchor
              __typename
            }
            variant
            is_ready
            hold_text
            __typename
          }
          ... on StructuredTextWidget {
            is_ready
            categories {
              ...StructuredTextCategory
              __typename
            }
            __typename
          }
          ... on SupportFormWidget {
            custom_options {
              option_key
              text
              email
              __typename
            }
            __typename
          }
          ... on Wifi4EUWidget {
            self_test
            network_identifier
            __typename
          }
          ... on EmergencyRequestWidget {
            reasons {
              reason
              __typename
            }
            disclaimer
            status
            __typename
          }
          ... on MovingMapWidget {
            is_ready
            icon
            geo_points {
              icon_width
              icon_url
              lat
              long
              text
              __typename
            }
            json
            __typename
          }
          __typename
        }
        fragment Anchor on Anchor {
          slug
          label
          __typename
        }
        fragment SimpleTextWidget on SimpleTextWidget {
          content
          enable_anchor
          anchor {
            ...Anchor
            __typename
          }
          __typename
        }
        fragment StructuredTextCategory on StructuredTextCategory {
          label
          entries {
            ...StructuredTextEntry
            __typename
          }
          enable_anchor
          anchor {
            ...Anchor
            __typename
          }
          __typename
        }
        fragment StructuredTextEntry on StructuredTextEntry {
          title
          content
          POI_match {
            ...PoiMatch
            __typename
          }
          __typename
        }
        fragment PoiMatch on PoiMatch {
          stop {
            name
            id
            ds100
            ibnr
            __typename
          }
          __typename
        }
    '''
    """The query to execute against the GraphQL API."""

    _user_session_id: str

    def __init__(self):
        ThreadedGraphQlAPI.__init__(self)
        try:
            response = requests.get(
                'https://unwired.info/?source=wasabi',
                headers={'User-Agent': 'Python/onboardapis (%s)' % get_package_version()}
            )
            self._user_session_id, *_ = parse_qs(urlparse(response.url).query)['user_session_id']
        except (ConnectionError, KeyError) as e:
            raise InitialConnectionError from e

    def refresh(self) -> None:
        response = self.execute(
            document=gql(self.UNWIRED_GRAPHQL_QUERY),
            variable_values={
                "widget_id": "363a8707-5e3e-4a5b-b565-9d22470dfd25",
                "language": "de",
                "user_session_id": self._user_session_id,
            }
        )

        journey = json.loads(response['feed_widget']['widget']['json'])
        self._data['journey'] = (
            {} if 'content' in journey.keys()  # No journey info found for your location!
            else journey['course']
        )


class GenericUnwiredInternetAccessInterface(InternetAccessInterface):
    def enable(self) -> None:  # TODO: implement
        pass

    def disable(self) -> None:  # TODO: implement
        pass
