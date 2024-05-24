from __future__ import annotations

import logging

from abc import ABCMeta

from ....mixins import InternetAccessMixin
from ... import Train
from .interfaces import GenericIcomeraAPI, GenericIcomeraInternetAccessInterface

logger = logging.getLogger(__name__)


class GenericIcomeraTrain(Train, InternetAccessMixin, metaclass=ABCMeta):
    _api: GenericIcomeraAPI
    _internet_access: GenericIcomeraInternetAccessInterface

    def __init__(self):
        if not hasattr(self, '_api'):
            self._api = GenericIcomeraAPI()
        if not hasattr(self, '_internet_access'):
            self._internet_access = GenericIcomeraInternetAccessInterface(self._api)
        Train.__init__(self)
        InternetAccessMixin.__init__(self)
