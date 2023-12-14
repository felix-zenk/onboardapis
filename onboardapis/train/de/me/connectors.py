from typing import TypedDict

from bs4 import BeautifulSoup

from ....data import RESTDataConnector, store

CaptivePortalInfo = TypedDict('CaptivePortalInfo', {
    'has_internet_access': bool,
})
CaptivePortalInfo.__doc__ = "A dict containing information about the state of the captive portal"


class CaptivePortalConnector(RESTDataConnector):
    """
    Connector for the captive portal of the Metronom trains.
    """

    API_URL = 'http://wifi.metronom.de'

    @store('captive_portal')
    def captive_portal(self) -> CaptivePortalInfo:
        soup = BeautifulSoup(self.get('de').text, 'html.parser')
        user_online = soup.find(class_='user-online', recursive=True)
        return CaptivePortalInfo(
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
