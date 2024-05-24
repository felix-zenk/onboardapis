from __future__ import annotations

import logging

from ...third_party.icomera import GenericIcomeraAPI, GenericIcomeraInternetAccessInterface

logger = logging.getLogger(__name__)


class MetronomAPI(GenericIcomeraAPI):
    # noinspection HttpUrlsUsage
    API_URL = 'http://wifi.metronom.de'


class MetronomInternetAccessInterface(GenericIcomeraInternetAccessInterface):
    # noinspection HttpUrlsUsage
    API_URL = 'http://wifi.metronom.de'
