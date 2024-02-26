from ....mixins import InternetAccessMixin
from ... import Train
from .connectors import MetronomCaptivePortalConnector, MetronomInternetAccessInterface


class MetronomCaptivePortal(InternetAccessMixin, Train):
    """
    Basically no information about the train.
    """
    _data: MetronomCaptivePortalConnector
    _internet_access: MetronomInternetAccessInterface

    def __init__(self) -> None:
        self._data = MetronomCaptivePortalConnector()
        self._internet_access = MetronomInternetAccessInterface()
