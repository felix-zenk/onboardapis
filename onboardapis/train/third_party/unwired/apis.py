from __future__ import annotations

import logging
import re

from abc import ABCMeta
from datetime import datetime, timedelta

from ....mixins import InternetAccessMixin
from ....data import ID
from ... import Train
from .interfaces import GenericUnwiredAPI

logger = logging.getLogger(__name__)


class GenericUnwiredTrain(Train, InternetAccessMixin):
    _api: GenericUnwiredAPI

    def __init__(self):
        Train.__init__(self)
        InternetAccessMixin.__init__(self)

    @property
    def id(self) -> ID:
        return self._api['journey']['id']

    @property
    def type(self) -> str:
        return re.match(r'(\w+)\d+', self._api['journey']['line']).group(1)

    @property
    def line_number(self) -> str:
        return re.match(r'\w+(\d+)', self._api['journey']['line']).group(1)
