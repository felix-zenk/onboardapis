from __future__ import annotations

import logging
import time

from functools import lru_cache
from typing import TypedDict

from deprecation import deprecated

from ....data import ThreadedRestAPI, store, get_package_version

logger = logging.getLogger(__name__)

Endpoints = TypedDict("Endpoints", {
    'api/train_info': int,
    'api/gps': dict,
    'api/speed': float,
})
"""A dict containing information about the endpoints of the Railnet API"""


class RailnetRegioAPI(ThreadedRestAPI):
    API_URL = "https://railnet.oebb.at"

    @store('train_info')
    @lru_cache
    def train_info(self) -> int:
        return int(self.get("api/trainInfo").text)

    @store('gps')
    def gps(self) -> dict:
        return self.get("api/gps").json()

    @store('speed')
    def speed(self) -> float:
        return float(self.get("api/speed").text)

    @deprecated(
        deprecated_in='2.0.0',
        removed_in='2.1.0',
        current_version=get_package_version(),
        details='combined has been removed from the API by ÖBB'
    )
    @store('combined')
    def combined(self) -> dict:
        return self.get("assets/modules/fis/combined.json", params={"_time": time.time()}).json()

    def refresh(self) -> None:
        self.train_info()
        self.gps()
        self.speed()
