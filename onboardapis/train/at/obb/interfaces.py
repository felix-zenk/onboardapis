from __future__ import annotations

import logging
import time

from functools import lru_cache
from typing import TypedDict

from ....data import ThreadedRestAPI, store
from ....exceptions import APIConnectionError

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

    @store('combined')
    def combined(self) -> dict:
        return self.get("assets/media/fis/combined.json", params={'_time': time.time_ns() / 10e6}).json()

    def refresh(self) -> None:
        # Use data from available sources, 'combined' is not available in every train
        try:
            self.combined()
        except APIConnectionError:
            self.train_info()
            self.gps()
            self.speed()
