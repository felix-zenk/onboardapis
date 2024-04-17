from __future__ import annotations

import logging

from abc import ABCMeta

from ....mixins import InternetAccessMixin
from ... import Train
from .interfaces import GenericIcomeraAPI

logger = logging.getLogger(__name__)


class GenericIcomeraTrain(Train, InternetAccessMixin, metaclass=ABCMeta):
    _api: GenericIcomeraAPI

    def __init__(self):
        Train.__init__(self)
        InternetAccessMixin.__init__(self)
