import logging

from bs4 import BeautifulSoup

from ....data import RESTDataConnector, InternetAccessInterface, SynchronousRESTDataConnector

logger = logging.getLogger(__name__)


class MetronomCaptivePortalConnector(RESTDataConnector):
    """
    Connector for the captive portal of the Metronom trains.
    """

    API_URL = 'http://wifi.metronom.de'

    def refresh(self) -> None:
        pass


class MetronomInternetAccessInterface(SynchronousRESTDataConnector, InternetAccessInterface):
    API_URL = 'http://wifi.metronom.de'

    def enable(self):
        soup = BeautifulSoup(self.get('de').text, 'html.parser')
        user_offline = soup.find(class_='user-offline', recursive=True)
        if user_offline is None:
            return

        csrf_token = soup.find('input', {'name': 'CSRFToken'}, recursive=True)['value']
        response = self.post('de', json={
            'CSRFToken': csrf_token,
            'login': True,
        })
        response.raise_for_status()
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-online', recursive=True) is None:
            raise ConnectionError('Login failed!')

    def disable(self):
        soup = BeautifulSoup(self.get('de').text, 'html.parser')
        user_online = soup.find(class_='user-online', recursive=True)
        if user_online is None:
            return

        csrf_token = user_online.find('input', {'name': 'CSRFToken'}, recursive=True)['value']
        response = self.post('de', json={
            'logout': True,
            'CSRFToken': csrf_token,
        })
        response.raise_for_status()
        if BeautifulSoup(response.text, 'html.parser').find(class_='user-offline', recursive=True) is None:
            raise ConnectionError('Logout failed!')

    @property
    def is_enabled(self) -> bool:
        return BeautifulSoup(
            self.get('de').text, 'html.parser'
        ).find(class_='user-online', recursive=True) is not None
