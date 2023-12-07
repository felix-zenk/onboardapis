from ... import IncompleteTrainMixin, Train

from .connectors import CaptivePortalConnector


class CaptivePortal(IncompleteTrainMixin, Train):
    """
    Basically no information about the train.
    """
    _data: CaptivePortalConnector

    def __init__(self) -> None:
        self._data = CaptivePortalConnector()

    @property
    def logged_in(self) -> bool:
        """
        Whether the client is logged in to the captive portal.
        """
        return self._data['captive_portal']['has_internet_access']
