from __future__ import annotations

import logging

from ...third_party.icomera import GenericIcomeraTrain
from ....mixins import InternetAccessMixin
from .interfaces import MetronomInternetAccessInterface

logger = logging.getLogger(__name__)


class MetronomCaptivePortal(GenericIcomeraTrain, InternetAccessMixin):
    _internet_access: MetronomInternetAccessInterface

    def __init__(self) -> None:
        GenericIcomeraTrain.__init__(self)
        InternetAccessMixin.__init__(self)
        self._internet_access = MetronomInternetAccessInterface()

    @property
    def type(self) -> str:
        return 'ME'
