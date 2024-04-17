from __future__ import annotations

import logging

from ...third_party.icomera import GenericIcomeraTrain
from ....mixins import InternetAccessMixin
from .interfaces import MetronomAPI, MetronomInternetAccessInterface

logger = logging.getLogger(__name__)


class MetronomCaptivePortal(GenericIcomeraTrain, InternetAccessMixin):
    _api: MetronomAPI
    _internet_access: MetronomInternetAccessInterface

    def __init__(self) -> None:
        self._api = MetronomAPI()
        self._internet_access = MetronomInternetAccessInterface()
        GenericIcomeraTrain.__init__(self)
        InternetAccessMixin.__init__(self)

    @property
    def type(self) -> str:
        return 'ME'
