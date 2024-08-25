from __future__ import annotations

import logging
import re

from ....exceptions import DataInvalidError
from ....mixins import InternetAccessMixin
from ... import Train
from .interfaces import GenericUnwiredAPI, GenericUnwiredInternetAccessInterface

logger = logging.getLogger(__name__)


class GenericUnwiredTrain(Train, InternetAccessMixin):
    _api: GenericUnwiredAPI
    _internet_access: GenericUnwiredInternetAccessInterface

    def __init__(self):
        if not hasattr(self, '_api'):
            self._api = GenericUnwiredAPI()
        if not hasattr(self, '_internet_access'):
            self._internet_access = GenericUnwiredInternetAccessInterface(self._api)
        Train.__init__(self)
        InternetAccessMixin.__init__(self)

    @property
    def id(self) -> str:
        if 'id' not in self._api['journey']:
            raise DataInvalidError('The trains ID could not be fetched from the server!')
        return self._api['journey']['id']

    @property
    def type(self) -> str:
        if 'line' not in self._api['journey']:
            raise DataInvalidError('The train type could not be fetched from the server!')
        return re.match(r'(\w+)\d+', self._api['journey']['line']).group(1)

    @property
    def line_number(self) -> str:
        if 'line' not in self._api['journey']:
            raise DataInvalidError('The line number could not be fetched from the server!')
        return re.match(r'\w+(\d+)', self._api['journey']['line']).group(1)
