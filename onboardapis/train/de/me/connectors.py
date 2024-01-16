from typing import TypedDict

from bs4 import BeautifulSoup

from ....data import RESTDataConnector, store

MetronomCaptivePortalInfo = TypedDict('MetronomCaptivePortalInfo', {
    'has_internet_access': bool,
})
"""A dict containing information about the state of the captive portal"""


class MetronomCaptivePortalConnector(RESTDataConnector):
    """
    Connector for the captive portal of the Metronom trains.
    """

    API_URL = 'http://wifi.metronom.de'

    @store('captive_portal')
    def captive_portal(self) -> MetronomCaptivePortalInfo:
        soup = BeautifulSoup(self.get('de').text, 'html.parser')
        user_online = soup.find(class_='user-online', recursive=True)
        return MetronomCaptivePortalInfo(
            has_internet_access=user_online is not None,
        )

    def refresh(self) -> None:
        self.captive_portal()

    def login(self) -> None:
        soup = BeautifulSoup(self.get('de').text, 'html.parser')
        user_offline = soup.find(class_='user-offline', recursive=True)
        if user_offline is None:
            return

        csrf_token = soup.find('input', {'name': 'CSRFToken'}, recursive=True)['value']
        self.post('de', data={
            'CSRFToken': csrf_token,
            'login': True,
        })
        self.captive_portal()

    def logout(self) -> None:
        soup = BeautifulSoup(self.get('de').text, 'html.parser')
        user_online = soup.find(class_='user-online', recursive=True)
        if user_online is None:
            return

        csrf_token = user_online.find('input', {'name': 'CSRFToken'}, recursive=True)['value']
        self.post('de', data={
            'CSRFToken': csrf_token,
            'logout': True,
        })
        self.captive_portal()
