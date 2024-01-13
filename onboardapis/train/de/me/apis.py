from ... import IncompleteTrainMixin, Train

from .connectors import MetronomCaptivePortalConnector


class MetronomCaptivePortal(IncompleteTrainMixin, Train):
    """
    Basically no information about the train.
    """
    _data: MetronomCaptivePortalConnector

    def __init__(self) -> None:
        self._data = MetronomCaptivePortalConnector()

    @property
    def logged_in(self) -> bool:
        """
        Whether the client is logged in to the captive portal.
        """
        return self._data['captive_portal']['has_internet_access']

    def do_login(self) -> None:
        """
        Log in to the captive portal.
        """
        self._data.login()

    def do_logout(self) -> None:
        """
        Log out from the captive portal.
        """
        self._data.logout()
