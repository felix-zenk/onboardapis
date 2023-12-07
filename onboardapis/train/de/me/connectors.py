from typing import TypedDict

from bs4 import BeautifulSoup

from ....data import RESTDataConnector, store

CaptivePortalInfo = TypedDict('CaptivePortalInfo', {
    'has_internet_access': bool,
})


class CaptivePortalConnector(RESTDataConnector):
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
