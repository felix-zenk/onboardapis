from __future__ import annotations

import logging

from abc import ABCMeta

from ....data import ThreadedRestAPI

logger = logging.getLogger(__name__)


class GenericIcomeraAPI(ThreadedRestAPI, metaclass=ABCMeta):
    # noinspection HttpUrlsUsage
    API_URL = 'http://omboard.info'
